-- ============================================================
-- 大学萌新领航站 - 数据库初始化脚本
-- 包含建表 + 测试数据
-- 使用方法：mysql -u root -p < init.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS campus_nav DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_nav;

-- ============================================================
-- 建表
-- ============================================================

CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `nickname` VARCHAR(50) NOT NULL COMMENT '昵称',
    `student_id` VARCHAR(20) DEFAULT NULL COMMENT '学号',
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'BCrypt 密码哈希',
    `college` VARCHAR(100) DEFAULT NULL COMMENT '学院',
    `major` VARCHAR(100) DEFAULT NULL COMMENT '专业',
    `grade` VARCHAR(10) DEFAULT NULL COMMENT '入学年份',
    `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像 URL',
    `role` VARCHAR(20) NOT NULL DEFAULT 'USER' COMMENT '角色',
    `status` INT NOT NULL DEFAULT 1 COMMENT '1正常 0禁用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_nickname` (`nickname`),
    UNIQUE KEY `uk_student_id` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE IF NOT EXISTS `course` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL COMMENT '课程名称',
    `teacher` VARCHAR(100) DEFAULT NULL COMMENT '授课教师',
    `college` VARCHAR(100) DEFAULT NULL COMMENT '开课学院',
    `category` VARCHAR(50) DEFAULT NULL COMMENT '课程类别',
    `credit` DECIMAL(3,1) DEFAULT NULL COMMENT '学分',
    `status` INT NOT NULL DEFAULT 1 COMMENT '1正常 0下架',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_course_college` (`college`),
    INDEX `idx_course_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程基础表';

CREATE TABLE IF NOT EXISTS `course_review` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `course_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `is_anonymous` INT NOT NULL DEFAULT 0 COMMENT '0实名 1匿名',
    `difficulty_rating` INT NOT NULL COMMENT '难度 1-5',
    `score_rating` INT NOT NULL COMMENT '给分 1-5',
    `content` TEXT NOT NULL COMMENT '评价正文',
    `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
    `status` INT NOT NULL DEFAULT 1 COMMENT '1正常 0被下架',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_review_course_id` (`course_id`),
    INDEX `idx_review_user_id` (`user_id`),
    INDEX `idx_review_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程评价表';

CREATE TABLE IF NOT EXISTS `review_comment` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `review_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `parent_id` BIGINT DEFAULT NULL COMMENT '回复的评论ID',
    `content` TEXT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_comment_review_id` (`review_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评价评论表';

CREATE TABLE IF NOT EXISTS `review_like` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `review_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_review_user` (`review_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='点赞记录表';

CREATE TABLE IF NOT EXISTS `review_report` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `review_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL COMMENT '举报人',
    `reason` VARCHAR(500) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='举报记录表';

CREATE TABLE IF NOT EXISTS `user_favorite` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `course_review_id` BIGINT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_review` (`user_id`, `course_review_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表';

CREATE TABLE IF NOT EXISTS `user_checkin` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `task_id` BIGINT NOT NULL,
    `checked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_task` (`user_id`, `task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户打卡表';

CREATE TABLE IF NOT EXISTS `club` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `category` VARCHAR(50) NOT NULL,
    `logo_url` VARCHAR(500) DEFAULT NULL,
    `description` TEXT,
    `activity_frequency` VARCHAR(100) DEFAULT NULL,
    `requirements` TEXT,
    `tips` TEXT COMMENT '防坑指南',
    `contact` VARCHAR(200) DEFAULT NULL,
    `status` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_club_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社团信息表';

CREATE TABLE IF NOT EXISTS `club_event` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `club_id` BIGINT NOT NULL,
    `title` VARCHAR(200) NOT NULL,
    `event_type` VARCHAR(50) DEFAULT NULL,
    `event_time` DATETIME NOT NULL,
    `location` VARCHAR(200) DEFAULT NULL,
    `description` TEXT,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_event_club_id` (`club_id`),
    INDEX `idx_event_time` (`event_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='社团活动表';

CREATE TABLE IF NOT EXISTS `poi` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL COMMENT '地标名称',
    `category` VARCHAR(50) NOT NULL,
    `description` TEXT,
    `photo_url` VARCHAR(500) DEFAULT NULL,
    `open_hours` VARCHAR(200) DEFAULT NULL,
    `floor_info` VARCHAR(500) DEFAULT NULL,
    `tips` TEXT,
    `lat` DECIMAL(10,7) DEFAULT NULL,
    `lng` DECIMAL(10,7) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_poi_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='校园地标表';

CREATE TABLE IF NOT EXISTS `poi_route` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `from_poi_id` BIGINT NOT NULL,
    `to_poi_id` BIGINT NOT NULL,
    `description` TEXT NOT NULL,
    `estimated_minutes` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_route_from_to` (`from_poi_id`, `to_poi_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路径指引表';

CREATE TABLE IF NOT EXISTS `poi_correction` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `poi_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `content` TEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='纠错记录表';

CREATE TABLE IF NOT EXISTS `guide` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `category` VARCHAR(50) NOT NULL,
    `content` JSON DEFAULT NULL COMMENT '步骤内容',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='攻略表';

CREATE TABLE IF NOT EXISTS `freshman_task` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `icon` VARCHAR(50) DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `badge_level` VARCHAR(20) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新生任务模板表';

CREATE TABLE IF NOT EXISTS `safety_tip` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `content` TEXT NOT NULL,
    `image_url` VARCHAR(500) DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `is_pinned` INT NOT NULL DEFAULT 0 COMMENT '是否置顶',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='安全防线表';


-- ============================================================
-- 测试数据
-- ============================================================

-- 管理员（密码：admin123，BCrypt 哈希）
INSERT INTO `user` (`nickname`, `password_hash`, `role`) VALUES
('admin', '$2b$12$LJ3m4ys3LkBCVxJGq.5qSOZx3qMfJWv6rZ3Kq8qF9wJmqiZT3Rn5q', 'ADMIN');

-- 测试用户（密码均为：123456）
-- 注意：实际 BCrypt 哈希通过 app 注册接口生成，此处用占位符
INSERT INTO `user` (`nickname`, `password_hash`, `college`, `major`, `grade`) VALUES
('张三', '$2b$12$eImiTXuWVxfM37uY4JANjOLZaD2qLQxRFqX3nOMdhYZK5LXqmj4Rm', '计算机学院', '软件工程', '2024'),
('李四', '$2b$12$eImiTXuWVxfM37uY4JANjOLZaD2qLQxRFqX3nOMdhYZK5LXqmj4Rm', '经济管理学院', '工商管理', '2024'),
('王五', '$2b$12$eImiTXuWVxfM37uY4JANjOLZaD2qLQxRFqX3nOMdhYZK5LXqmj4Rm', '外国语学院', '英语', '2024');

-- 课程
INSERT INTO `course` (`name`, `teacher`, `college`, `category`, `credit`) VALUES
('高等数学A（上）', '刘教授', '数学学院', '通识必修', 5.0),
('大学英语I', '陈老师', '外国语学院', '通识必修', 3.0),
('程序设计基础', '张教授', '计算机学院', '专业必修', 4.0),
('微观经济学', '王教授', '经济管理学院', '通识选修', 3.0),
('大学物理B', '赵教授', '物理学院', '通识必修', 4.0),
('线性代数', '周教授', '数学学院', '通识必修', 3.0),
('思想道德与法治', '李老师', '马克思主义学院', '通识必修', 2.0),
('数据结构与算法', '钱教授', '计算机学院', '专业必修', 4.0);

-- 课程评价
INSERT INTO `course_review` (`course_id`, `user_id`, `is_anonymous`, `difficulty_rating`, `score_rating`, `content`, `like_count`) VALUES
(1, 2, 0, 4, 3, '刘老师讲课非常深入，但考试难度确实不低。建议课前预习，课后及时复习，不然很容易跟不上节奏。期中考试主要考察计算能力，期末考试侧重证明题。', 15),
(1, 3, 1, 5, 4, '数学渣慎选！！！讲的飞快，考试题巨难，不过老师给分还行，有平时分撑着', 8),
(3, 2, 0, 3, 5, '张老师人很好，零基础也能跟上。每节课都有编程练习，期末是个小项目。强烈推荐！', 22),
(5, 4, 0, 3, 4, '赵老师的物理课很有激情，实验课也很有意思。考试难度适中，认真学基本都能过。', 10),
(4, 4, 0, 2, 5, '王老师的微观经济学讲得通俗易懂，案例丰富。考试开卷，只要上课听了就能过。', 12),
(8, 2, 1, 4, 4, '数据结构确实有难度，但钱老师讲解很清晰。实验课非常重要，期末项目占了40%的分。建议多做LeetCode练手。', 18);

-- 社团
INSERT INTO `club` (`name`, `category`, `description`, `activity_frequency`, `requirements`, `tips`, `contact`) VALUES
('计算机协会', '学术科技', '面向全校的计算机技术交流社团，涵盖编程、网络安全、AI等多个方向。每周有技术分享会，每学期举办黑客马拉松。', '每周一次技术分享', '对计算机感兴趣即可，无门槛', '零基础也可以加入，学长学姐会手把手教。不要被"计算机"三个字吓到。', 'QQ群：123456789'),
('青年志愿者协会', '志愿公益', '组织各类志愿服务活动，包括支教、敬老、环保、社区服务等。累计志愿时长可兑换第二课堂学分。', '每两周一次活动', '有爱心、有责任心', '志愿活动名额有限，看到通知要及时报名。部分活动可以加综测分。', '微信：volunteer2024'),
('街舞社', '文体艺术', '校园最具活力的舞蹈社团，涵盖Hiphop、Breaking、Jazz、Popping等舞种。零基础教学，每学期有专场演出。', '每周三次训练', '热爱舞蹈，能坚持训练', '训练强度较大，建议准备两套运动服。期末有考核，但主要是看进步。', '社长微信：danceclub'),
('英语角', '学术科技', '提升英语口语和跨文化交流能力的社团。每周有英语角自由交谈，定期举办英语演讲比赛和电影之夜。', '每周一次英语角', '能用英语进行基本交流', '不要怕说错，大家都是来练习的。可以和外教、留学生交朋友。', 'QQ群：888777666'),
('摄影协会', '文体艺术', '用镜头记录校园生活的美好瞬间。定期组织外拍活动、摄影技巧培训和作品展览。', '每两周一次外拍', '有相机或手机均可', '没有相机也没关系，手机摄影也能出大片。协会可以借用设备。', '微信：photoclub2024');

-- 社团活动
INSERT INTO `club_event` (`club_id`, `title`, `event_type`, `event_time`, `location`) VALUES
(1, '计算机协会招新宣讲会', '宣讲会', '2025-09-15 19:00:00', '教学楼A101'),
(1, '新生编程入门工作坊', '开放日', '2025-09-22 14:00:00', '计算机实验楼301'),
(2, '青协新学期动员大会', '宣讲会', '2025-09-16 18:30:00', '大学生活动中心'),
(3, '街舞社体验课', '开放日', '2025-09-18 16:00:00', '体育馆舞蹈房'),
(4, '英语角迎新特别活动', '开放日', '2025-09-20 15:00:00', '图书馆咖啡厅');

-- POI 地标
INSERT INTO `poi` (`name`, `category`, `description`, `open_hours`, `floor_info`, `tips`) VALUES
('第一教学楼', '教学楼', '学校最主要的教学楼，承担大部分理论课程的授课任务。教室分为多媒体教室、阶梯教室和研讨室三种类型。', '7:00 - 22:00', '共6层：1-2层为大阶梯教室，3-4层为多媒体教室，5-6层为研讨室和教师办公室', '考试周开放至23:00；教室内禁止饮食'),
('图书馆', '教学楼', '学校标志性建筑，藏书200万册。设有自习区、电子阅览室、小组讨论室和咖啡厅。', '8:00 - 22:00（周末9:00-21:00）', '共5层：1层大厅+咖啡厅，2-3层社科图书，4层自科图书，5层电子阅览室+自习区', '需刷校园卡进入；考试周需提前占座'),
('第一食堂', '食堂', '离教学区最近的食堂，主打中式快餐。一楼为自选窗口，二楼为特色小吃。', '早餐6:30-9:00，午餐11:00-13:00，晚餐17:00-19:00', '1层：自选窗口；2层：麻辣香锅、兰州拉面、黄焖鸡等特色窗口', '高峰期排队较长，建议错峰就餐；支持校园卡和支付宝'),
('菜鸟驿站', '快递点', '校内快递收发中心，支持顺丰、中通、圆通、韵达等主流快递。', '9:00 - 20:00', '位于学生宿舍区入口处，独立平房', '取件需出示取件码或校园卡；大件物品可借用手推车'),
('体育馆', '运动场馆', '综合性体育场馆，包含篮球场、羽毛球场、乒乓球室、健身房和游泳池。', '8:00 - 21:30', '1层：游泳馆；2层：篮球场+羽毛球场；3层：乒乓球室+健身房', '部分场馆需提前预约；健身房凭校园卡免费使用'),
('行政楼', '行政楼', '学校行政办公中心，教务处、学生处、财务处等均在此办公。', '8:30-12:00，14:00-17:30（工作日）', '共8层：1层大厅+保卫处，2层教务处，3层学生处，4层财务处', '办理业务注意办公时间，多数窗口午休不办公'),
('校医院', '其他', '校内基础医疗服务中心，可处理常见病症和外伤，支持医保报销。', '8:00-12:00，14:00-17:30（急诊24小时）', '1层：挂号+门诊+药房；2层：输液室+观察室', '带好校园卡和医保卡；夜间急诊走侧门');

-- POI 路径
INSERT INTO `poi_route` (`from_poi_id`, `to_poi_id`, `description`, `estimated_minutes`) VALUES
(1, 2, '从第一教学楼正门出发，沿银杏路向南直行约200米，经过喷泉广场后左转，继续走100米即可看到图书馆。', 5),
(1, 3, '从第一教学楼北门出发，沿梧桐路向西直行约300米，经过篮球场后右转，食堂在左手边。', 7),
(2, 3, '从图书馆正门出发，沿银杏路向北走到喷泉广场，右转进入梧桐路，直行200米到篮球场左转即到。', 8);

-- 攻略
INSERT INTO `guide` (`title`, `category`, `content`) VALUES
('新生报到流程', '办事流程',
'[{"step":1,"title":"到达学校","description":"按录取通知书上的报到日期到达学校。各大火车站/汽车站有学校接站大巴。","location_poi_id":null},{"step":2,"title":"找到所属学院接待点","description":"各学院在图书馆广场设有新生接待点，找到自己学院的帐篷，领取报到指引单。","location_poi_id":2},{"step":3,"title":"办理宿舍入住","description":"凭报到指引单到宿舍楼管理员处领取钥匙，安置行李。","location_poi_id":null},{"step":4,"title":"缴纳学费（如未线上缴费）","description":"到行政楼财务处缴纳学费，或通过学校官方公众号线上缴费。","location_poi_id":6},{"step":5,"title":"领取校园卡","description":"到行政楼学生处领取校园卡，校园卡是校内消费和门禁的唯一凭证。","location_poi_id":6},{"step":6,"title":"完成报到","description":"将盖章后的报到指引单交回学院接待点，报到完成！","location_poi_id":null}]'
),
('校医院看病报销流程', '办事流程',
'[{"step":1,"title":"挂号","description":"携带校园卡到校医院1楼挂号窗口挂号。","location_poi_id":7},{"step":2,"title":"就诊","description":"按号到对应诊室就诊，医生开具处方或检查单。","location_poi_id":7},{"step":3,"title":"缴费取药","description":"到收费窗口缴费（医保直接结算），然后到药房取药。","location_poi_id":7},{"step":4,"title":"转诊（如需）","description":"如需到校外医院就诊，医生开具转诊单，保留所有发票回来报销。","location_poi_id":7},{"step":5,"title":"报销（校外就医后）","description":"携带转诊单、发票、病历到行政楼财务处医保窗口报销。","location_poi_id":6}]'
);

-- 新生任务
INSERT INTO `freshman_task` (`title`, `description`, `icon`, `sort_order`, `badge_level`) VALUES
('完成报到注册', '按照新生报到流程完成所有注册步骤', 'DocumentChecked', 10, NULL),
('参加开学典礼', '参加学校统一组织的开学典礼', 'Star', 20, NULL),
('参观图书馆', '到图书馆参观并了解借阅规则', 'Reading', 30, 'bronze'),
('加入一个社团', '选择至少一个感兴趣的社团并参加活动', 'UserFilled', 40, 'silver'),
('了解食堂窗口', '探索学校各个食堂的特色美食', 'Food', 50, NULL),
('完成选课', '在教务系统完成本学期选课', 'Edit', 60, 'bronze'),
('参加军训', '完成新生军训任务', 'Sunny', 70, 'silver'),
('认识3位新朋友', '主动社交，扩展朋友圈', 'ChatRound', 80, NULL),
('使用图书馆自习', '在图书馆完成一次自习', 'Clock', 90, 'bronze'),
('参加一次校园活动', '参加学校或学院组织的文体/学术活动', 'Trophy', 100, 'gold');

-- 安全防线
INSERT INTO `safety_tip` (`title`, `content`, `sort_order`, `is_pinned`) VALUES
('防诈骗提醒：这些套路要警惕！', '1. 任何以"学长/学姐"名义推销电话卡、培训班的都要提高警惕；\n2. 不要向任何人透露银行卡密码和验证码；\n3. 所谓"老师"电话要求转账的一律是诈骗；\n4. 网上刷单、兼职先交钱的都是骗局；\n5. 遇到可疑情况第一时间联系辅导员或拨打校园报警电话。', 0, 1),
('宿舍消防安全须知', '1. 宿舍内严禁使用大功率电器（热得快、电磁炉等）；\n2. 禁止在宿舍内给电动车电池充电；\n3. 离开宿舍时关闭所有电源；\n4. 不在床上吸烟、不使用明火；\n5. 熟悉宿舍楼消防通道和灭火器位置。', 10, 1),
('校园紧急电话', '校园110：010-8888-0110\n校医院急诊：010-8888-0120\n心理咨询中心：010-8888-1234\n学生处值班：010-8888-5678', 20, 1),
('校园夜间出行安全', '1. 尽量避免深夜单独出行；\n2. 走有路灯的大路，避开偏僻小路；\n3. 记住校园110电话，设置为一键拨号；\n4. 晚归可结伴同行或使用校园巡逻车护送服务。', 30, 0);

SELECT '数据库初始化完成！' AS message;
