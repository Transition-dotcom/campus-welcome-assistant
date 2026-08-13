#!/bin/bash
# 大学萌新领航站 全流程 E2E 冒烟测试（针对真实 MySQL + 真实后端）
BASE="http://localhost:8080"
PASS=0; FAIL=0; FAILED_NAMES=()

check() { # name, condition_result(0/1)
  local name="$1"; local ok="$2"
  if [ "$ok" -eq 0 ]; then PASS=$((PASS+1)); echo "✅ $name"
  else FAIL=$((FAIL+1)); FAILED_NAMES+=("$name"); echo "❌ $name"; fi
}

jqget() { jq -r "$1" 2>/dev/null; }

# ── 0. 系统 ──
R=$(curl -s $BASE/); echo "$R" | jq -e '.message' >/dev/null 2>&1; check "GET / 服务状态" $?
R=$(curl -s $BASE/health); echo "$R" | jq -e '.database=="connected"' >/dev/null 2>&1; check "GET /health 数据库连接" $?

# ── 1. 注册与登录 ──
NICK="e2e$RANDOM"
R=$(curl -s -X POST $BASE/api/user/register -H 'Content-Type: application/json' -d "{\"nickname\":\"$NICK\",\"password\":\"Passw0rd123\"}")
AT=$(echo "$R" | jqget '.tokens.access_token'); RT=$(echo "$R" | jqget '.tokens.refresh_token'); UID_=$(echo "$R" | jqget '.user.id')
[ -n "$AT" ] && [ "$AT" != "null" ]; check "POST 注册并返回双 token" $?

R=$(curl -s -X POST $BASE/api/user/login -H 'Content-Type: application/json' -d '{"nickname":"admin","password":"admin123"}')
ADM=$(echo "$R" | jqget '.tokens.access_token')
[ -n "$ADM" ] && [ "$ADM" != "null" ]; check "POST 管理员登录 admin/admin123" $?

R=$(curl -s -X POST $BASE/api/user/login -H 'Content-Type: application/json' -d '{"nickname":"admin","password":"wrongpass"}')
[ "$(echo "$R" | jqget '.detail')" = "昵称或密码错误" ]; check "错误密码返回统一提示（防枚举）" $?

# ── 2. 课程评价链路 ──
R=$(curl -s "$BASE/api/courses?page=1&page_size=50")
TOTAL=$(echo "$R" | jqget '.total'); [ "$TOTAL" = "25" ]; check "课程列表 total=25（种子数据）" $?

R=$(curl -s "$BASE/api/courses/1/reviews?page_size=50")
RTOTAL=$(echo "$R" | jqget '.total'); [ "$RTOTAL" -ge 1 ] 2>/dev/null; check "课程 1 有种子评价" $?

R=$(curl -s -X POST $BASE/api/courses/1/reviews -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' \
  -d '{"difficulty_rating":3,"score_rating":4,"content":"E2E 测试匿名评价，内容足够长", "is_anonymous":true}')
RID=$(echo "$R" | jqget '.id'); ANON_UID=$(echo "$R" | jqget '.user_id')
[ -n "$RID" ] && [ "$RID" != "null" ]; check "POST 发表匿名评价" $?
[ "$ANON_UID" = "null" ]; check "匿名评价响应 user_id=null（不泄漏）" $?

R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/like -H "Authorization: Bearer $AT")
LIKED=$(echo "$R" | jqget '.is_liked'); [ "$LIKED" = "true" ]; check "POST 点赞" $?
R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/like -H "Authorization: Bearer $AT")
[ "$(echo "$R" | jqget '.is_liked')" = "false" ]; check "POST 取消点赞（toggle）" $?

R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/favorite -H "Authorization: Bearer $AT")
[ "$(echo "$R" | jqget '.is_favorited')" = "true" ]; check "POST 收藏评价" $?
R=$(curl -s $BASE/api/courses/favorites/my -H "Authorization: Bearer $AT")
echo "$R" | jq -e --argjson rid "$RID" '.items | map(select(.review_id==$rid or .id==$rid)) | length > 0' >/dev/null 2>&1
check "GET 我的收藏包含刚收藏的评价" $?
R=$(curl -s -X POST $BASE/api/courses/reviews/99999/favorite -H "Authorization: Bearer $AT")
[ "$(echo "$R" | jqget '.detail')" != "null" ]; check "收藏不存在评价 → 4xx" $?

R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/comments -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"content":"一级评论"}')
CID=$(echo "$R" | jqget '.id')
R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/comments -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d "{\"content\":\"二级回复\",\"parent_id\":$CID}")
[ "$(echo "$R" | jqget '.parent_id')" = "$CID" ]; check "POST 楼中楼回复" $?
R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/comments -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"content":"非法回复","parent_id":999999}')
ST=$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/courses/reviews/$RID/comments -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"content":"非法回复","parent_id":999999}')
[ "$ST" = "404" ] || [ "$ST" = "400" ]; check "parent_id 不存在 → 4xx（防跨楼）" $?

R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/report -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"reason":"E2E 测试举报内容"}')
[ "$(echo "$R" | jqget '.message')" != "null" ]; check "POST 举报评价" $?
R=$(curl -s -X POST $BASE/api/courses/reviews/$RID/report -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"reason":"重复举报测试"}')
[ "$(echo "$R" | jqget '.detail')" != "null" ]; check "重复举报被拦截" $?

# ── 3. 社团 / 活动（验证相对时间种子） ──
R=$(curl -s "$BASE/api/clubs?page_size=50")
[ "$(echo "$R" | jqget '.total')" = "15" ]; check "社团列表 total=15" $?
R=$(curl -s "$BASE/api/clubs/events/upcoming")
EV=$(echo "$R" | jq 'length'); [ "$EV" -ge 3 ] 2>/dev/null; check "近期活动非空（DATE_ADD 种子生效，$EV 场）" $?
R=$(curl -s -G "$BASE/api/clubs" --data-urlencode "keyword=甲骨文")
[ "$(echo "$R" | jqget '.total')" -ge 1 ] 2>/dev/null; check "社团模糊搜索" $?

# ── 4. POI / 路径 / 纠错 ──
R=$(curl -s "$BASE/api/pois?page_size=50")
[ "$(echo "$R" | jqget '.total')" = "14" ]; check "地标列表 total=14" $?
R=$(curl -s "$BASE/api/pois/routes/list")
[ "$(echo "$R" | jq 'length')" -ge 1 ] 2>/dev/null; check "路径指引非空" $?
R=$(curl -s -X POST $BASE/api/pois/correction -H "Authorization: Bearer $AT" -H 'Content-Type: application/json' -d '{"poi_id":1,"content":"E2E 纠错：开放时间有误"}')
[ "$(echo "$R" | jqget '.message')" != "null" ] || [ "$(echo "$R" | jqget '.id')" != "null" ]; check "POST 提交地标纠错" $?

# ── 5. 攻略 / 任务 / 安全 / 首页 ──
R=$(curl -s "$BASE/api/guides")
[ "$(echo "$R" | jq 'length')" = "4" ]; check "攻略列表 4 篇" $?
R=$(curl -s "$BASE/api/guides/1")
[ "$(echo "$R" | jqget '.summary')" != "null" ]; check "攻略详情含 summary 字段" $?
R=$(curl -s "$BASE/api/tasks")
[ "$(echo "$R" | jq 'length')" = "12" ]; check "任务模板 12 项" $?
R=$(curl -s -X POST $BASE/api/tasks/1/checkin -H "Authorization: Bearer $AT")
[ "$(echo "$R" | jqget '.completed')" = "1" ]; check "POST 任务打卡" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/tasks/1/checkin -H "Authorization: Bearer $AT")
[ "$ST" = "400" ]; check "重复打卡 → 400" $?
R=$(curl -s "$BASE/api/safety-tips")
[ "$(echo "$R" | jq 'length')" -ge 1 ] 2>/dev/null; check "安全防线非空" $?
R=$(curl -s "$BASE/api/dashboard" -H "Authorization: Bearer $AT")
[ "$(echo "$R" | jqget '.task_progress.completed')" -ge 1 ] 2>/dev/null; check "仪表盘个性化任务进度（completed≥1）" $?

# ── 6. 全局搜索 ──
R=$(curl -s -G "$BASE/api/search" --data-urlencode "keyword=数学")
[ "$(echo "$R" | jqget '.total')" -ge 1 ] 2>/dev/null; check "搜索「数学」有结果" $?
echo "$R" | jq -e '[.items[].type] | index("course")' >/dev/null 2>&1; check "搜索结果按类型分组（含 course）" $?
R=$(curl -s -G "$BASE/api/search" --data-urlencode "keyword=高数")
echo "$R" | jq -e '[.items[] | select(.title | contains("高等数学"))] | length > 0' >/dev/null 2>&1; check "搜索缩写「高数」→「高等数学」" $?

# ── 7. 管理后台链路 ──
R=$(curl -s "$BASE/api/admin/reports?status=pending" -H "Authorization: Bearer $ADM")
RPID=$(echo "$R" | jqget '.items[0].id')
[ -n "$RPID" ] && [ "$RPID" != "null" ]; check "举报进入管理后台列表" $?
R=$(curl -s -X POST $BASE/api/admin/reports/$RPID/resolve -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"action":"remove_review"}')
[ "$(echo "$R" | jqget '.message')" != "null" ]; check "举报处理（下架评价）" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/courses/1/reviews?page_size=50")
R=$(curl -s "$BASE/api/courses/1/reviews?page_size=50")
echo "$R" | jq -e --argjson rid "$RID" '[.items[].id] | index($rid) | not' >/dev/null 2>&1
check "被下架评价不再出现在列表" $?

R=$(curl -s -X POST $BASE/api/admin/guides -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' \
  -d '{"title":"E2E 测试攻略","category":"办事流程","summary":"E2E 摘要","content":[{"step":1,"title":"第一步","description":"测试"}]}')
GID=$(echo "$R" | jqget '.id')
[ -n "$GID" ] && [ "$GID" != "null" ]; check "POST 管理员创建攻略（含 summary）" $?
R=$(curl -s "$BASE/api/admin/guides?page_size=50" -H "Authorization: Bearer $ADM")
echo "$R" | jq -e --argjson gid "$GID" '[.items[].id] | index($gid)' >/dev/null 2>&1; check "攻略出现在管理列表" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE $BASE/api/admin/guides/$GID -H "Authorization: Bearer $ADM")
[ "$ST" = "200" ]; check "DELETE 攻略" $?

R=$(curl -s -X POST $BASE/api/admin/tasks -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' \
  -d '{"title":"E2E 测试任务","description":"测试","icon":"Star","sort_order":130}')
TID=$(echo "$R" | jqget '.id')
R=$(curl -s -X PUT $BASE/api/admin/tasks/$TID -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"title":"E2E 任务已改名"}')
[ "$(echo "$R" | jqget '.title')" = "E2E 任务已改名" ]; check "PUT 修改任务" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE $BASE/api/admin/tasks/$TID -H "Authorization: Bearer $ADM")
[ "$ST" = "200" ]; check "DELETE 任务" $?

R=$(curl -s "$BASE/api/admin/corrections" -H "Authorization: Bearer $ADM")
CRID=$(echo "$R" | jqget '.[0].id')
[ -n "$CRID" ] && [ "$CRID" != "null" ]; check "纠错进入管理后台" $?
R=$(curl -s -X PUT $BASE/api/admin/corrections/$CRID/resolve -H "Authorization: Bearer $ADM")
[ "$(echo "$R" | jqget '.message')" != "null" ]; check "纠错标记已处理" $?

# ── 8. 用户禁用 → 旧 token 失效 → 重新启用 ──
ST=$(curl -s -o /dev/null -w '%{http_code}' -X PUT $BASE/api/admin/users/$UID_/status -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"status":0}')
[ "$ST" = "200" ]; check "PUT 禁用用户" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' $BASE/api/user/profile -H "Authorization: Bearer $AT")
[ "$ST" = "401" ]; check "禁用后旧 access_token 立即 401" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' -X PUT $BASE/api/admin/users/$UID_/status -H "Authorization: Bearer $ADM" -H 'Content-Type: application/json' -d '{"status":1}')
[ "$ST" = "200" ]; check "PUT 重新启用用户" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' $BASE/api/user/profile -H "Authorization: Bearer $AT")
[ "$ST" = "200" ]; check "启用后原 token 恢复可用" $?

# ── 9. refresh token 轮换 ──
R=$(curl -s -X POST $BASE/api/user/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT\"}")
RT2=$(echo "$R" | jqget '.refresh_token')
[ -n "$RT2" ] && [ "$RT2" != "null" ] && [ "$RT2" != "$RT" ]; check "POST 刷新 token（轮换新 refresh）" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/user/refresh -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$RT\"}")
[ "$ST" = "401" ]; check "旧 refresh_token 复用 → 401（轮换撤销）" $?

# ── 10. 越权与校验 ──
ST=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/admin/users" -H "Authorization: Bearer $AT")
[ "$ST" = "403" ]; check "普通用户访问管理接口 → 403" $?
ST=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/search?keyword=a")
[ "$ST" = "422" ]; check "搜索关键词过短 → 422" $?

echo ""
echo "════════════════════════════════"
echo "通过 $PASS 项 / 失败 $FAIL 项"
if [ $FAIL -gt 0 ]; then printf '失败项: %s\n' "${FAILED_NAMES[@]}"; fi
exit $FAIL
