-- ============================================================
-- 大学萌新领航站 - 东北大学软件学院定制版
-- 基于东北大学浑南校区公开信息 + 软件学院培养方案
-- 使用方法：mysql -u root -proot < init.sql
-- 可重复执行：每次导入都会重建数据库，重置为干净的演示数据
-- ============================================================

DROP DATABASE IF EXISTS campus_nav;
CREATE DATABASE campus_nav DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_nav;

-- ============================================================
-- 建表（同上版本，保持不变）
-- ============================================================

CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `nickname` VARCHAR(50) NOT NULL,
    `student_id` VARCHAR(20) DEFAULT NULL COMMENT '学号',
    `password_hash` VARCHAR(255) NOT NULL,
    `college` VARCHAR(100) DEFAULT NULL COMMENT '学院',
    `major` VARCHAR(100) DEFAULT NULL COMMENT '专业',
    `grade` VARCHAR(20) DEFAULT NULL COMMENT '入学年份',
    `avatar_url` VARCHAR(500) DEFAULT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'USER',
    `status` INT NOT NULL DEFAULT 1,
    `token_version` INT NOT NULL DEFAULT 0 COMMENT 'token版本号，刷新时+1，旧token失效',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_nickname` (`nickname`),
    UNIQUE KEY `uk_student_id` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

CREATE TABLE IF NOT EXISTS `course` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NOT NULL,
    `teacher` VARCHAR(100) DEFAULT NULL,
    `college` VARCHAR(100) DEFAULT NULL,
    `category` VARCHAR(50) DEFAULT NULL,
    `credit` DECIMAL(4,2) DEFAULT NULL,
    `status` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_course_college` (`college`),
    INDEX `idx_course_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程基础表';

CREATE TABLE IF NOT EXISTS `course_review` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `course_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `is_anonymous` INT NOT NULL DEFAULT 0,
    `difficulty_rating` INT NOT NULL,
    `score_rating` INT NOT NULL,
    `content` TEXT NOT NULL,
    `like_count` INT NOT NULL DEFAULT 0,
    `status` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_review_course_id` (`course_id`),
    INDEX `idx_review_user_id` (`user_id`),
    INDEX `idx_review_created_at` (`created_at`),
    INDEX `idx_review_hot` (`status`, `like_count`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程评价表';

CREATE TABLE IF NOT EXISTS `review_comment` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `review_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `parent_id` BIGINT DEFAULT NULL,
    `content` TEXT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_comment_review_id` (`review_id`),
    INDEX `idx_comment_parent_id` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评价评论表';

CREATE TABLE IF NOT EXISTS `review_like` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `review_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_review_user` (`review_id`, `user_id`),
    INDEX `idx_like_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='点赞记录表';

CREATE TABLE IF NOT EXISTS `review_report` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `review_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `reason` VARCHAR(500) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_report_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='举报记录表';

CREATE TABLE IF NOT EXISTS `user_favorite` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `course_review_id` BIGINT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_review` (`user_id`, `course_review_id`),
    INDEX `idx_favorite_review_id` (`course_review_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表';

CREATE TABLE IF NOT EXISTS `user_checkin` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `task_id` BIGINT NOT NULL,
    `checked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_task` (`user_id`, `task_id`),
    INDEX `idx_checkin_user_id` (`user_id`),
    INDEX `idx_checkin_task_id` (`task_id`)
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
    `name` VARCHAR(200) NOT NULL,
    `category` VARCHAR(50) NOT NULL,
    `description` TEXT,
    `photo_url` VARCHAR(500) DEFAULT NULL,
    `open_hours` VARCHAR(200) DEFAULT NULL,
    `floor_info` VARCHAR(500) DEFAULT NULL,
    `tips` TEXT,
    `lat` DECIMAL(10,7) DEFAULT NULL,
    `lng` DECIMAL(10,7) DEFAULT NULL,
    `status` INT NOT NULL DEFAULT 1 COMMENT '1正常 0下架（软删除）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_poi_category` (`category`),
    INDEX `idx_poi_name` (`name`)
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
    PRIMARY KEY (`id`),
    INDEX `idx_correction_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='纠错记录表';

CREATE TABLE IF NOT EXISTS `guide` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `category` VARCHAR(50) NOT NULL,
    `summary` VARCHAR(500) DEFAULT NULL,
    `content` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_guide_category` (`category`),
    INDEX `idx_guide_title` (`title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='攻略表';

CREATE TABLE IF NOT EXISTS `freshman_task` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `icon` VARCHAR(50) DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `badge_level` VARCHAR(20) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_task_sort` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新生任务模板表';

CREATE TABLE IF NOT EXISTS `safety_tip` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `content` TEXT NOT NULL,
    `image_url` VARCHAR(500) DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `is_pinned` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_safety_pinned_sort` (`is_pinned`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='安全防线表';


-- ============================================================
-- 测试数据 - 东北大学软件学院定制版
-- ============================================================

-- 管理员（密码：admin123）
INSERT INTO `user` (`nickname`, `password_hash`, `college`, `major`, `role`) VALUES
('admin', '$2b$12$YZJTjwbEnCCF5aAWVSr4UeHTXCnmWVHf1u34Ajhlf/Q21nwrq3CFm', '软件学院', '软件工程', 'ADMIN');


-- ============================================================
-- 课程数据 - 基于东北大学软件学院培养方案
-- ============================================================

-- 课程数据 - 依据《软件学院本科生各专业培养方案》（软件工程/特色班/国际班/信息安全/数字媒体技术）
INSERT INTO `course` (`id`, `name`, `teacher`, `college`, `category`, `credit`) VALUES
-- 通识必修（数学/外语/思政）
(1,  '高等数学①㈠',  NULL, '理学院', '通识必修', 5.0),
(2,  '高等数学①㈡',  NULL, '理学院', '通识必修', 5.0),
(3,  '线性代数',      NULL, '理学院', '通识必修', 3.0),
(4,  '概率论与数理统计', NULL, '理学院', '通识必修', 3.5),
(5,  '大学英语㈠',    NULL, '外国语学院', '通识必修', 4.0),
(6,  '思想道德与法治', NULL, '马克思主义学院', '通识必修', 3.0),

-- 专业必修（软件工程核心）
(7,  '程序设计基础',  NULL, '软件学院', '专业必修', 3.0),
(8,  '面向对象程序设计', NULL, '软件学院', '专业必修', 2.75),
(9,  '数据结构与算法', NULL, '软件学院', '专业必修', 3.5),
(10, '计算机组成原理', NULL, '软件学院', '专业必修', 3.5),
(11, '操作系统',      NULL, '软件学院', '专业必修', 2.25),
(12, '计算机网络',    NULL, '软件学院', '专业必修', 2.0),
(13, '数据库概论',    NULL, '软件学院', '专业必修', 2.5),
(14, '软件工程',      NULL, '软件学院', '专业必修', 3.5),
(15, '软件需求分析与设计', NULL, '软件学院', '专业必修', 2.0),
(16, '软件质量保证与测试', NULL, '软件学院', '专业必修', 2.25),

-- 专业选修（软件工程/前沿方向）
(17, '软件项目管理与过程改进', NULL, '软件学院', '专业选修', 2.0),
(18, '算法分析与设计', NULL, '软件学院', '专业选修', 2.25),
(19, '人工智能技术',  NULL, '软件学院', '专业选修', 2.0),
(20, '深度学习导论',  NULL, '软件学院', '专业选修', 2.0),
(21, 'Web开发技术',   NULL, '软件学院', '专业选修', 2.75),

-- 信息安全方向（专业分流后选修）
(22, '密码学基础',    NULL, '软件学院', '专业选修', 2.0),
(23, '网络与系统安全', NULL, '软件学院', '专业选修', 3.25),

-- 数字媒体技术方向
(24, '计算机图形学',  NULL, '软件学院', '专业必修', 3.5),
(25, '数字媒体美术基础', NULL, '软件学院', '专业选修', 2.75);


-- ============================================================
-- 课程评价 - 模拟老生经验
-- ============================================================

INSERT INTO `course_review` (`course_id`, `user_id`, `is_anonymous`, `difficulty_rating`, `score_rating`, `content`, `like_count`, `created_at`) VALUES
(7, 1, 0, 2, 5, '程序设计基础是软院的第一门编程课，从零开始完全没问题，每节课都有上机练习。期末是大作业，做个小游戏或者管理系统。强烈推荐大一上学期认真学，后续所有课程都要用编程基础。', 25, NOW() - INTERVAL 15 DAY),
(7, 1, 1, 3, 4, '虽然是入门课但内容不少，函数和结构体部分要好好理解。老师会提供office hour答疑，建议多去。', 10, NOW() - INTERVAL 12 DAY),
(9, 1, 0, 4, 4, '数据结构与算法是软院学分最重的课之一。老师要求比较严格，但讲得很清楚。实验课占40%，LeetCode刷题很有帮助。期末笔试有一定难度，红黑树和B+树重点看。', 20, NOW() - INTERVAL 13 DAY),
(9, 1, 1, 5, 3, '数据结构真的好难，期末前通宵复习。但是学好了对后面的课程和找实习帮助巨大，咬牙坚持吧。', 8, NOW() - INTERVAL 10 DAY),
(13, 1, 0, 3, 4, '数据库概论课上得很有条理，SQL语句和ER图设计是重点。课程设计用MySQL做一个完整的数据库应用，建议找好队友。', 15, NOW() - INTERVAL 9 DAY),
(14, 1, 0, 3, 5, '软件工程课绝对是软院最有价值的课之一！老师会模拟真实项目流程，从需求分析到测试交付完整走一遍。小组合作很重要，选对组员成功一半。', 18, NOW() - INTERVAL 8 DAY),
(10, 1, 1, 5, 3, '计组真的硬核，从数电到CPU设计，实验课写Verilog写到怀疑人生。不过学完对整个计算机体系理解会上一个台阶。', 12, NOW() - INTERVAL 7 DAY),
(11, 1, 0, 4, 4, '操作系统课内容量大，进程管理、内存管理、文件系统三大块。老师讲课幽默风趣，PintOS实验是亮点，能动手实现一个迷你OS。', 14, NOW() - INTERVAL 5 DAY),
(1, 1, 1, 3, 4, '高等数学是学分最高的课，5个学分！老师讲课节奏比较快，建议课前看书预习。期中考试计算为主，期末偏证明。成绩公式：(平时30%+期中30%+期末40%)', 20, NOW() - INTERVAL 3 DAY),
(3, 1, 0, 3, 4, '线性代数对于后续机器学习方向很重要。老师要求比较严，矩阵运算和特征值要练熟。考试题型比较固定，刷往年题有效。', 13, NOW() - INTERVAL 1 DAY);


-- ============================================================
-- 社团数据 - 基于软件学院及东北大学实际社团
-- ============================================================

INSERT INTO `club` (`name`, `category`, `description`, `activity_frequency`, `requirements`, `tips`, `contact`) VALUES
('甲骨文（Oracle）技术俱乐部', '学术科技',
 '由Oracle公司与东北大学共同支持的技术社团。下设主席团、技术部、项目部、外联部、宣传部、办公室、财务部七大部门。技术方向涵盖.NET、PHP、C++、JS、Linux、平面设计、网站开发、应用软件、游戏开发等。博士+研究生+本科生梯队式管理，有教师指导。',
 '每周一次技术分享，每月一次项目评审',
 '软件/计算机相关专业学生，对技术有热情即可',
 '零基础也可以参加，俱乐部有完整的培训体系。参加俱乐部可以获得Oracle官方认证的培训资源，对简历加分很有帮助。',
 'QQ群：请关注学院通知'),
('NEX信息安全创新团队', '学术科技',
 '东三省高校第一梯队的信息安全竞赛团队，全国大学生信息安全竞赛累计获一等奖5项。专攻密码破解、WEB漏洞挖掘、二进制分析、信息隐藏、流量分析、电子取证等方向。2024年获挑战杯"揭榜挂帅"特等奖。成员就业去向：字节跳动、绿盟等；深造去向：清华、上交、华科、中科院。',
 '每周专项训练，赛前集中备赛',
 '对信息安全有兴趣，有CTF基础或愿意从零学习',
 '没有CTF基础也没关系，团队有完整的入门培训。但需要足够的时间和热情投入，备赛期间可能很忙。历年指导教师：徐剑、王冬琦。',
 '关注NEX团队招新公告'),
('软件学院学生创新创业基地', '学术科技',
 '学院官方创新创业平台，统筹组织"挑战杯"、"互联网+"、"大创"等竞赛。2024年省级以上竞赛获奖632项（全校第一）。基地提供项目孵化、导师对接、经费支持等全链条服务。',
 '每学期组织竞赛申报，不定期举办讲座',
 '软件学院在籍学生',
 '大一就可以参加大创项目，提前积累项目经验。参加竞赛不仅能加分保研，对找实习也很有帮助。基地有专门的指导教师可以帮忙联系项目。',
 '软件学院学工办'),
('软件学院学生会', '学生组织',
 '软件学院学生会是服务全院同学的核心学生组织。在这里，你可以锻炼学生工作能力，结识志同道合的伙伴，收获丰富独特的活动体验，也能得到学长学姐的指导与帮助。

【下设部门】
办公室：协调各部门工作，承担各部门之间的纽带联络工作；负责学院各学生组织的组织相关工作，统筹内部行政事务。
学习部：开展各类益智类文体学习活动；负责部分公众号推文撰写；协助组织开展学院学生代表大会，营造良好的学院学习氛围。
外联部：协助其他学生组织开展各类活动；管理学院仓库，负责活动物资采购等相关保障工作。
体育部：组织开展学院各类体育赛事活动；负责校级体育比赛、校运动会的选手选拔与报名组织工作，丰富同学们的体育课余生活。',
 NULL,
 '1. 希望锻炼个人综合能力，勇于尝试学生工作；
2. 乐于结交同辈伙伴，拥有良好的沟通协作意识；
3. 对校园活动充满热情，愿意参与活动策划与落地；
4. 积极向上，愿意为学院同学服务，共建丰富多彩的校园生活。',
 NULL,
 NULL),
('学术促进会', '学术科技',
 '东北大学全校性学术社团，2024-2025连续两年获评"先进学生社团"。组织学术讲座、论文写作培训、科研方法分享、跨学科学术交流等活动。',
 '每两周一次学术沙龙',
 '全校学生均可参加',
 '参加学术促进会对了解科研方向、联系导师很有帮助。大二大三有保研意向的同学尤其推荐加入。',
 '东北大学学生社团联合会'),
('KAB创业俱乐部', '创新创业',
 '东北大学创新创业类学生社团，2025年获评"先进学生社团"。组织创业沙龙、商业计划书培训、创业路演等活动。与学校创新创业学院有密切合作。',
 '每月一次创业沙龙，每学期一次路演',
 '对创业感兴趣即可',
 '即使不创业，参加KAB也能锻炼商业思维和演讲能力。软院学生有技术优势，+商业思维=更有竞争力。',
 '东北大学创新创业学院'),
('羽毛球社团', '文体艺术',
 '东北大学羽毛球爱好者聚集地，2025年获评"先进学生社团"。每周组织训练和友谊赛，每学期有校内联赛。浑南校区风雨操场内有免费羽毛球场。',
 '每周两次训练',
 '热爱羽毛球即可，有一定基础优先',
 '风雨操场场地免费但需提前预约，社团有固定的训练时间段。入社需要自备球拍，社团提供训练用球。',
 'QQ群：关注社团招新'),
('东北大学大学生艺术团话剧团', '文体艺术',
 '东北大学官方艺术团下属话剧团体，2025年获评"优秀大学生艺术团"。每学期排演一到两部话剧，在校内剧场公演。曾多次在辽宁省大学生戏剧节获奖。',
 '每周排练3-4次，演出前集中排练',
 '对话剧表演或幕后制作有兴趣',
 '不需要表演基础，幕后岗位（灯光、音效、道具）同样需要人。排演期间时间投入较大，要提前规划好学习。',
 '大学生艺术团招新群');


-- ============================================================
-- 学生组织 - 软件学院八大院级学生组织（2026 招新）
-- ============================================================

INSERT INTO `club` (`name`, `category`, `description`, `activity_frequency`, `requirements`, `tips`, `contact`) VALUES
('软件学院团委', '学生组织',
 '软件学院团委是学院负责青年思想引领、团务管理、校园学生活动组织的核心学生组织。这里汇聚一批志同道合的青年学子，为广大同学提供充实有趣、共同进步的成长实践平台。

【下设部门】
组织部：负责团组织生活会开展、团支部理论学习等团务工作，落实学院基层团支部各项基础团务，推动青年理论学习工作落地执行。
素质拓展部：统筹学院各团支部相关工作，策划并组织开展各类素质拓展活动，丰富同学们课余生活，助力学生综合素养提升。
办公室：主要负责智慧团建系统管理、团费收缴、青年大学习统计等基础团务；同时承担团委内部行政事务、资料整理归档等后勤保障工作。
社会实践部：负责学生寒暑假社会实践项目的申报、进度跟踪以及成果宣传工作，组织引导同学们参与社会实践，积累课外实践经历。
第二课堂活动认证部：负责全院学生第二课堂成绩的管理、数据导入与审核工作，维护第二课堂数据，保障同学们课外活动学分认定工作有序开展。',
 NULL,
 '1. 渴望结交志同道合的朋友，具备团队协作意识；
2. 热爱校园活动，愿意参与活动策划、执行等相关工作；
3. 向往充实向上、共同进步的大学生活；
4. 思想觉悟端正，希望在学生工作中锻炼能力，实现自我成长。',
 NULL,
 NULL),
('软件学院文艺中心', '学生组织',
 '软件学院文艺中心是学院负责文艺晚会、文化活动策划落地的学生组织。这里是怀揣文艺梦想同学的起航平台，在这里你可以找到志同道合的伙伴，发挥创意才干，在活动幕后不断精进自我，收获成长与荣誉。

【下设部门】
艺术设计部：负责学院各类大型晚会的幕后实施与设计工作，完成晚会视觉、舞台相关设计落地，为文艺活动提供创意支撑。
秘书部：承担各类晚会的报账工作，负责活动奖品采购与发放，做好物资、财务相关后勤保障，保障文艺活动顺利开展。
策划部：负责学院各类文艺活动的幕后策划工作，构思活动方案，统筹活动流程，是每一场精彩活动的幕后智囊。',
 NULL,
 '1. 怀揣文艺梦想，对晚会、文艺活动抱有兴趣；
2. 富有创意想法，愿意参与活动策划、设计相关工作；
3. 做事认真细心，具备团队协作意识，可以配合团队完成幕后工作；
4. 渴望锻炼自我，希望在学生工作中收获成长与荣誉。',
 NULL,
 NULL),
('软件学院新媒体中心', '学生组织',
 '新媒体中心是软件学院官方微信公众号背后的学生运营组织。无论你是摄影、剪辑、写作、绘画方面的资深爱好者，还是零基础萌新，这里都是提升综合能力的优质平台。我们以文字、镜头、创意记录学院大小事件，运营学院线上宣传阵地。

【下设部门】
策划部：拟定新媒体中心活动方案，撰写活动策划案与公众号推文文本内容。
运营部：运营学院公众号内容，负责推文排版发布、视频号作品管理，承担晚会线上转播相关工作。
设计部：设计制作活动平面物料，包括舞台背景、门票等；打造学院专属红包封面等特色视觉产品，熟练运用PS等设计工具。
技术部：制作原创影视化视频，涵盖前期拍摄规划、后期剪辑特效；负责晚会中控、直播技术保障以及现场录制工作。
调研部：跟进学院各项活动，现场拍摄记录，完成照片后期处理与素材整理，为公众号供稿供图。',
 NULL,
 '1. 对文案写作、摄影摄像、剪辑、平面设计、视频创作抱有兴趣；
2. 零基础也可，愿意主动学习新媒体相关技能；
3. 做事认真负责，具备团队协作意识，乐于服务学院宣传工作；
4. 富有创意，希望用作品记录丰富多彩的校园生活。',
 NULL,
 NULL),
('软件学院学生发展委员会（学发委）', '学生组织',
 '软件学院学生发展委员会（简称学发委），致力于服务全院学生学业成长、心理健康与学生帮扶工作。秉持“嘤其鸣矣，求其友声”的理念，围绕学术交流、心理健康教育、资助帮扶、生涯规划开展各类学生服务工作，为同学们搭建成长交流的平台。

【下设部门】
媒体部：负责活动宣传全流程；完成招新海报制作、视频拍摄剪辑；运营“软”心声电台，做好组织对外宣传工作。
活动部：组织开展心理健康、学术交流等各类主题活动；撰写活动策划案，完成活动参与名单存档、审核工作。
办公室：维护更新学院贫困生电子档案，组织落实资助相关工作；负责成长发展指导员、心理委员、学发委成员的选聘、管理、考评，收集整理心理相关材料。
能量站：负责能量站日常预约与运营；组织导师预约、朋辈学长学姐预约；开展生涯规划主题系列活动；管理能量站图书借阅工作。',
 NULL,
 '1. 热心服务同学，关注学业、心理、资助相关学生工作；
2. 对文案宣传、活动策划感兴趣，愿意学习相关技能；
3. 做事细心严谨，可以完成档案整理、材料汇总类工作；
4. 善于沟通协作，希望在服务他人的过程中实现自我成长。',
 NULL,
 NULL),
('软件学院志愿者协会（志协）', '学生组织,志愿公益',
 '软件学院志愿者协会，简称志协，是学院开展志愿服务工作的学生组织。协会为同学们提供参与志愿服务的平台与机遇，鼓励同学们展现个人特长、奉献爱心，在志愿实践中锻炼自我、成就更好的自己。

【下设部门】
宣传部：负责志愿活动现场摄像工作，完成活动推文制作，做好各类志愿活动的宣传输出。
办公室：负责活动报备、信息整理，统计志愿者服务时长，做好内部资料归档管理。
日常活动部：负责校内志愿活动的策划与组织落地，开展各类校园志愿服务项目。
对外联系部：负责校外志愿活动的联系、组织与策划，拓展校外志愿服务资源。
“明光筑梦”志愿服务队：志协特色项目部门，对接云南、甘肃地区，帮扶偏远山区小朋友，助力山区孩子全面发展。',
 NULL,
 '1. 心怀公益热忱，愿意投身志愿服务；
2. 具备团队协作意识，做事踏实认真；
3. 愿意学习宣传、活动组织、对外沟通相关技能；
4. 希望在志愿实践中奉献自我，收获成长。',
 NULL,
 NULL),
('软件学院学生科学技术协会（科协）', '学生组织,学术科技',
 '东北大学软件学院学生科学技术协会，由学院团委领导，是软件学院重要的学生组织。下设办公室、对外事务部、科技竞赛部、学术发展部、创新创业部、创意科普部六个部门。各部门分工明确，协同运转，开展日常管理、内外交流、竞赛组织、学术提升、双创推动及创意科普等工作，为全院师生搭建成长与技术交流的实践平台。

【下设部门】
办公室：统筹科协日常事务，管理例会、人员与制度，运维双创基地，对接班级双创委员。
对外事务部：联结校内外资源，承办科普讲座、竞赛专题活动，拓展对外交流渠道。
科技竞赛部：主办软件专业竞赛，包含算法编程、信息安全类赛事，以赛促学，提升同学们专业实操能力。
学术发展部：策划刷题、趣味编程类活动，助力同学们提升学习与编程能力，营造良好学术氛围。
创新创业部：组织双创类竞赛，激发创新思维，为创业者对接资源，推动创新创业项目落地。
创意科普部：筹办创意节、科普节，点燃软件学子的双创与科学探索兴趣。',
 NULL,
 '1. 对编程、竞赛、科创、科普抱有兴趣，零基础也可以参与；
2. 做事严谨负责，拥有良好的团队协作能力；
3. 乐于参与讲座、竞赛、活动策划，希望提升自身专业综合能力。',
 NULL,
 NULL),
('软件学院自我管理委员会（自管会）', '学生组织',
 '软件学院自我管理委员会（自管会）是服务同学们日常生活、寝室管理的学生组织。秉持“我的校园我做主，自律自强共成长”的理念，致力于打造文明和谐的寝室与校园环境，策划生活类文化活动，邀请全体同学一同共建美好校园。

【下设部门】
寝室文化部：负责每月查寝工作，协同其他部门举办一年一度寝室文化节，建设优良寝室氛围。
新闻中心：负责微信推送、后台管理、图文制作；开展活动宣传、摄像、海报表格制作；完成每月查寝结果公示，承担自管会全部宣传工作。
秘书处：负责日常管理、会议记录、年度考核、活动考勤，撰写学期与年度工作总结；协助各部门开展工作，发挥桥梁纽带作用。
文化活动部：策划举办和寝室生活、学生日常生活相关的各类文化活动，丰富同学们课余生活。',
 NULL,
 '1. 关心寝室与校园生活，有服务同学的意识；
2. 细心踏实，能够完成查寝、文案、物料制作等工作；
3. 善于沟通协作，愿意参与活动策划，乐于奉献；
4. 希望在学生工作中锻炼自我，共建舒适校园环境。',
 NULL,
 NULL);


-- ============================================================
-- 社团活动 - 模拟招新时间线
-- event_time 使用相对当前时间（DATE_ADD(NOW(), INTERVAL n DAY)），
-- 保证任何时候初始化数据库，招新日历都不会因过期时间被 event_time >= NOW() 过滤为空。
-- ============================================================

INSERT INTO `club_event` (`club_id`, `title`, `event_type`, `event_time`, `location`) VALUES
(1, '甲骨文俱乐部招新宣讲 & 技术体验', '宣讲会', DATE_ADD(NOW(), INTERVAL 2 DAY), '信息学馆A101'),
(1, 'Oracle数据库入门工作坊', '开放日', DATE_ADD(NOW(), INTERVAL 5 DAY), '1号教学楼B区机房'),
(2, 'NEX团队CTF新生体验赛', '开放日', DATE_ADD(NOW(), INTERVAL 7 DAY), '信息学馆网络安全实验室'),
(2, 'NEX团队秋季招新面试', '面试', DATE_ADD(NOW(), INTERVAL 11 DAY), '信息学馆A209'),
(4, '软件学院学生会干事招新', '面试', DATE_ADD(NOW(), INTERVAL 3 DAY), '信息学馆A103'),
(3, '创新创业基地大创项目说明会', '宣讲会', DATE_ADD(NOW(), INTERVAL 9 DAY), '信息学馆A101'),
(5, '学术促进会新学期首次学术沙龙', '开放日', DATE_ADD(NOW(), INTERVAL 13 DAY), '图书馆咖啡厅'),
(6, 'KAB创业俱乐部创业idea路演', '开放日', DATE_ADD(NOW(), INTERVAL 16 DAY), '学生生活服务中心多功能厅'),
(7, '羽毛球社新生体验赛', '开放日', DATE_ADD(NOW(), INTERVAL 20 DAY), '风雨操场羽毛球馆'),
(8, '话剧团《雷雨》秋季公演', '开放日', DATE_ADD(NOW(), INTERVAL 25 DAY), '浑南校区学生剧场'),
(9, '软件学院团委招新宣讲会', '宣讲会', DATE_ADD(NOW(), INTERVAL 4 DAY), '信息学馆A201'),
(10, '文艺中心新生才艺招募', '开放日', DATE_ADD(NOW(), INTERVAL 8 DAY), '学生生活服务中心多功能厅'),
(11, '新媒体中心拍摄与剪辑体验课', '开放日', DATE_ADD(NOW(), INTERVAL 12 DAY), '信息学馆B209'),
(12, '学发委朋辈导师见面会', '开放日', DATE_ADD(NOW(), INTERVAL 15 DAY), '图书馆咖啡厅'),
(13, '志协志愿服务项目宣讲', '宣讲会', DATE_ADD(NOW(), INTERVAL 18 DAY), '1号教学楼A102'),
(14, '科协新生编程挑战赛', '开放日', DATE_ADD(NOW(), INTERVAL 22 DAY), '信息学馆机房'),
(15, '自管会寝室文化节启动', '开放日', DATE_ADD(NOW(), INTERVAL 28 DAY), '学生宿舍区广场'),
(1, '甲骨文俱乐部二次招新面试', '面试', DATE_ADD(NOW(), INTERVAL 35 DAY), '信息学馆A101'),
(2, 'NEX团队春季招新宣讲', '宣讲会', DATE_ADD(NOW(), INTERVAL 45 DAY), '信息学馆A101'),
(5, '学术促进会论文写作工作坊', '开放日', DATE_ADD(NOW(), INTERVAL 55 DAY), '图书馆研讨室');


-- ============================================================
-- POI 地标数据 - 基于东北大学浑南校区实际建筑
-- ============================================================

INSERT INTO `poi` (`name`, `category`, `description`, `open_hours`, `floor_info`, `tips`) VALUES
-- 教学与学术建筑
('1号教学楼', '教学楼',
 '浑南校区最主要的公共教学楼，分A、B两区。A区为阶梯大教室（100-200人），承担大部分公共课和大班授课；B区为小教室及计算机机房，主要用于上机实践课和自习。所有教室均配备空调和多媒体设备。',
 '6:00 - 22:00',
 'A区：阶梯大教室（1-3层）；B区：小教室及实验机房（1-5层）',
 '考试周开放至23:00。A区和B区之间有连廊通道，雨天不用走外面。每层都有饮水机和自动售货机。'),
('图书馆', '教学楼',
 '由中国建筑设计研究院副院长崔恺院士设计。外观为古朴的红砖色调，与东北大学历史感融为一体。藏书涵盖工、理、管、文各学科。设有自习区、电子阅览室、小组讨论室和咖啡厅。借期60天，可续借一次（延长30天），本科生可同时借15册。',
 '周一至周日 7:30-22:00（寒暑假 8:30-16:30）',
 '1层：门厅+报告厅+24小时阅览室；2层：中央大厅+检索区+咖啡书吧；3层：社科图书（A-K类）；4层：科技图书（N-Z类）+电子阅览室；5层：外文图书+研修室（5楼B区）',
 '考试周需提前占座，建议8:00前到。讨论室需在网上预约系统提前预约。图书馆WiFi信号全校最好。'),
('信息学馆（信息科学大楼）', '教学楼',
 '四大学馆之一，软件学院、计算机科学与工程学院的主要办公和教学场所。学院行政办公室、教授工作室、实验室均设在此。大部分专业课和实验课在信息学馆进行。',
 '6:00 - 22:30',
 'A区：软件学院行政+教授办公室；B区：实验室+研究生工作室',
 '软院学生大部分时间都在信息学馆度过。学馆内有自动售货机和饮水机。A区1楼有学院公告栏，重要通知都在上面。'),
('生命学馆（生命科学大楼）', '教学楼',
 '四大学馆之一，位于校区东北区。生命科学与健康学院、医学与生物信息工程学院所在地。部分通识选修课和跨学院课程在此授课。',
 '6:00 - 22:30',
 '1-2层：教室+实验室；3-5层：学院行政+教授办公室',
 '距离宿舍区稍远，上课记得提前出发。1楼有咖啡机。'),
('文管学馆（文科1楼）', '教学楼',
 '四大学馆之一。文法学院、马克思主义学院、工商管理学院所在地。思想道德与法治、大学英语等通识课在此授课。',
 '6:00 - 22:30',
 '1-2层：大教室+阶梯教室；3-5层：学院办公室',
 '文管学馆的教室普遍比较新，多媒体设备好用。1楼大厅有沙发休息区。'),
('建筑学馆（文科2楼）', '教学楼',
 '四大学馆之一，由清华大学建筑学院院长庄惟敏教授设计。江河建筑学院所在地。建筑本身极具设计感，是浑南校区的标志性建筑之一。',
 '6:00 - 22:30',
 '1层：展厅+设计工作室；2-4层：教室+模型制作室',
 '建筑学馆本身就是一个景点，值得参观。经常有学生设计作品展，对外开放。'),

-- 生活设施
('浑南校区食堂', '食堂',
 '浑南校区主要就餐场所。一楼提供早中晚三餐，经济实惠；二楼设有小火锅/冷面店、学府餐厅（可点菜聚餐）；三楼为风味档口，麻辣香锅、兰州拉面、黄焖鸡等。另有教工餐厅和回民餐厅。',
 '早餐 6:30-8:50，午餐 11:00-13:00，晚餐 16:30-18:40（三楼至20:30）',
 '1层：基础窗口（自选快餐）；2层：特色餐厅+小火锅；3层：风味档口',
 '高峰期11:50-12:20排队最长，建议错峰。手机支付：支付宝/微信均可。回民餐厅在食堂东侧单独入口。'),
('学生生活服务中心', '其他',
 '浑南校区的生活服务综合体。内设超市、浴池、快递站（乐收）、文印中心、理发室、眼镜店等，满足学生日常生活需求。',
 '超市至晚自习结束，浴池周二至周日12:00-22:00（周一维护）',
 '1层：超市+快递站D106+文印中心D107+理发室D103/105；2层：浴池',
 '快递站（乐收）营业时间7:30-19:00。取件需出示取件码。大件快递可以借用手推车。浴池周一不开放，注意安排时间。'),
('校医院', '其他',
 '浑南校区基础医疗服务中心。可处理常见病症（感冒、肠胃炎等）和外伤。支持大学生医保报销。急诊随时可诊。',
 '门诊 8:30-19:00，急诊 24小时',
 '1层：挂号+门诊+药房+输液室',
 '首次就诊需带校园卡和身份证建档。医保报销需保留所有票据。急诊夜间走东侧门。浑南卫生所电话：024-83656263。'),

-- 运动设施
('风雨操场（体育馆）', '运动场馆',
 '浑南校区综合体育场馆。内设羽毛球馆、室内篮球场、排球场、健身房、台球室。所有设施凭校园卡免费使用。冬季室外操场可改作滑冰场。',
 '7:00 - 21:00',
 '1层：羽毛球馆+篮球场+排球场；2层：健身房+台球室+乒乓球室',
 '部分场馆需提前预约。健身房凭校园卡免费，人多时段需排队。冬季滑冰鞋出租5元（凭学生证）。新生体测在此进行。'),

-- 校园景观
('小南湖公园', '其他',
 '浑南校区的核心景观区，位于宿舍楼群附近。夏季满塘荷花盛开，湖畔柳树成荫，是晨读、散步、约会的好去处。冬季湖面结冰，可观赏冰上落日。',
 '全天开放',
 '环湖步道约800米，有长椅和凉亭',
 '最佳观赏时间：夏季6-7月荷花季，秋季10月银杏季。湖边蚊子多，夏天记得带驱蚊水。晚上灯光略暗，女生尽量结伴。'),
('浑南校区北门', '其他',
 '浑南校区主要校门之一，正对风雨操场。是学生出入校园最常用的校门。北门外有公交站和多条线路经过。',
 '24小时开放',
 '门卫室+刷卡闸机',
 '进出需刷校园卡。北门外有共享单车停放点。打车定位选"东北大学浑南校区北门"。'),
('浑南校区西门', '其他',
 '浑南校区西门，门外有夜市（步行即达），是学生晚上吃夜宵的首选出口。',
 '6:00 - 23:00',
 '门卫室+刷卡闸机',
 '西门外夜市推荐：烤冷面、铁板鱿鱼、炸鸡架。建议结伴出行，注意食品安全。'),

-- 宿舍
('学生宿舍区', '宿舍',
 '浑南校区已投入使用1-5号宿舍楼，均为四人间。层高3.6米（国内高校最高），框架结构防震8级，陶土砖砌筑。上床下桌，配备空调，WIFI全覆盖。每层有公共卫生间、热水机、洗衣机、公共活动空间。寝室东侧为A区，西侧为B区。',
 '6:00 - 23:00（门禁）',
 '四人间+独立阳台，每层设有公共卫浴+开水机+洗衣机',
 '23:00后回宿舍需登记。洗衣机扫码使用（每次3-5元）。宿舍电费通过校园卡充值。大功率电器（热得快、电磁炉等）严禁使用，宿管会不定期检查。');


-- ============================================================
-- POI 路径指引 - 热门路线
-- ============================================================

INSERT INTO `poi_route` (`from_poi_id`, `to_poi_id`, `description`, `estimated_minutes`) VALUES
(14, 1, '从宿舍区出发，沿银杏路向北直行约400米，经过小南湖公园左转，继续走200米即可看到1号教学楼。', 8),
(14, 7, '从宿舍区出发向西直行约200米，食堂在右手边。这是宿舍到食堂的最短路线。', 3),
(14, 2, '从宿舍区出发沿银杏路向北，至喷泉广场右转，沿银杏大道直行约300米到图书馆。', 10),
(1, 3, '从1号教学楼北门出发，沿梧桐路向东步行约300米，信息学馆在左手边。', 5),
(7, 2, '从食堂出发沿银杏大道向西直行约200米，经过喷泉广场，图书馆在右手边。', 4),
(14, 10, '从宿舍区出发向西直行约300米，经过食堂后继续向前，风雨操场在左手边。', 6),
(7, 8, '从食堂出西门，学生生活服务中心就在食堂西侧紧邻，步行1分钟。', 1),
(3, 7, '从信息学馆出发向西直行约300米，经过喷泉广场后右转，食堂在右手边。', 6);


-- ============================================================
-- 攻略 - 新生办事流程（东北大学软件学院定制）
-- ============================================================

INSERT INTO `guide` (`title`, `category`, `summary`, `content`) VALUES
('新生报到注册流程', '办事流程', '从接站到领校园卡，七步搞定报到全流程',
'[{"step":1,"title":"抵达浑南校区","description":"按录取通知书日期到达东北大学浑南校区（沈阳市浑南区创新路195号）。沈阳站/沈阳北站/桃仙机场均有学校接站大巴。自驾可导航至浑南校区北门。","location_poi_id":12},{"step":2,"title":"找到软件学院接待点","description":"各学院在图书馆前广场设有新生接待帐篷。找到软件学院的蓝色帐篷，出示录取通知书和身份证，领取报到指引单和校园卡。","location_poi_id":2},{"step":3,"title":"办理宿舍入住","description":"凭报到指引单到宿舍楼一楼管理员处领取房间钥匙。浑南校区宿舍均为四人间上床下桌，配备空调和WIFI。A区（东侧）B区（西侧）根据学院分配。","location_poi_id":14},{"step":4,"title":"缴纳费用（如未线上缴费）","description":"学费和住宿费可通过东北大学财务处公众号线上缴费。如需现场缴费，到学生生活服务中心财务窗口办理。学费标准：软件工程专业大一、大二 5200 元/年，大三、大四 16000 元/年（按学年预收）。","location_poi_id":8},{"step":5,"title":"领取军训服装","description":"凭校园卡到风雨操场领取军训服装（迷彩服、帽子、腰带、胶鞋），当场试穿，不合适可以调换。","location_poi_id":10},{"step":6,"title":"参加新生见面会","description":"各班级会在报到当天或第二天组织新生见面会，由辅导员和班级导师主持，介绍学院情况和近期安排。地点通常在信息学馆。","location_poi_id":3},{"step":7,"title":"完成报到","description":"将盖章后的报到指引单交回学院接待点，正式成为东北大学软件学院的一员！关注「东大软件」微信公众号获取后续通知。","location_poi_id":null}]'
),
('图书馆借阅指南', '办事流程', '检索、找书、借还、续借，图书馆使用一步到位',
'[{"step":1,"title":"开通借阅权限","description":"新生入学后，图书馆借阅权限自动开通。无需单独办理。如无法刷卡进入，到图书馆1楼服务台激活。","location_poi_id":2},{"step":2,"title":"检索图书","description":"在图书馆2层中央大厅的检索终端或通过东北大学图书馆微信公众号检索需要的图书。记下索书号和馆藏位置。","location_poi_id":2},{"step":3,"title":"找书","description":"根据索书号到对应楼层找书。社科图书（A-K类）在3层，科技图书（N-Z类）在4层。找不到可以问服务台工作人员。","location_poi_id":2},{"step":4,"title":"自助借还","description":"在自助借还机上刷校园卡，按屏幕提示操作。借期60天，可续借一次（延长30天）。本科生最多同时借15册。","location_poi_id":2},{"step":5,"title":"还书&超期处理","description":"到期前归还到自助还书机。超期不罚款，实行停借处理（超一天停一天）。如遇寒暑假，还书日期自动顺延到开学后一周。","location_poi_id":2}]'
),
('选课操作指南', '学习攻略', '初选→退选→补选，三轮选课全流程详解',
'[{"step":1,"title":"查看培养方案","description":"登录东北大学教务系统（jwxt.neu.edu.cn），查看软件学院本专业的培养方案。了解必修课、选修课学分要求和开课学期。软件学院按计算机类大类招生，第2学期末专业分流，可选软件工程、信息安全、数字媒体技术，以及软件工程（金融科技特色方向）班。","location_poi_id":null},{"step":2,"title":"关注选课通知","description":"教务处每学期第16周左右发布下学期选课通知。注意选课分为三轮：初选→退选→补选（同学们也常称预选/正选/补退选）。错过初选还可以在补选阶段补报。","location_poi_id":null},{"step":3,"title":"初选阶段","description":"在教务系统中提交选课志愿。热门课（给分高的老师）会超额，系统抽签决定。建议选2-3个备选方案。","location_poi_id":null},{"step":4,"title":"退选阶段","description":"初选结果公布后可退掉不想要的课程。退选后进入补选，可重新选择尚有余额的课程，建议尽早登录。软院的专业课通常不会超额。","location_poi_id":null},{"step":5,"title":"补选（期初/期中）","description":"补选分期初、期中两次。开学后听过第一节课如不满意，可退课或换课。注意必修课不能退，选修课退课后需确保总学分达标。","location_poi_id":null}]'
),
('校医院就诊&医保报销', '办事流程', '挂号、就诊、转诊、报销，看病与医保攻略',
'[{"step":1,"title":"挂号","description":"携带校园卡和身份证到校医院1楼挂号窗口挂号。挂号费约4-6元（校园卡结算）。首诊需建档。","location_poi_id":9},{"step":2,"title":"就诊","description":"按号到对应诊室就诊。常见病症（感冒发烧、肠胃炎、外伤）可在校医院直接处理。","location_poi_id":9},{"step":3,"title":"缴费取药","description":"到收费窗口缴费，医保即时结算。凭处方到药房取药。校医院药品种类有限，特殊药品需到校外药店购买。","location_poi_id":9},{"step":4,"title":"转诊（如需）","description":"如需到校外医院就诊，由校医院医生开具转诊单，到二级及以上医院就诊方可报销。距离校区最近的是中国医科大学附属盛京医院（浑南院区）。保留所有发票和病历用于报销。","location_poi_id":9},{"step":5,"title":"医保报销","description":"校外就诊后，携带转诊单、发票、费用清单、病历复印件到学生活动中心医保窗口申请报销。公费医疗门诊报销50%；大学生医保住院在特三级医院（含盛京医院）报销70%。每年有报销截止日期，注意及时办理。","location_poi_id":8}]'
);


-- ============================================================
-- 新生任务清单 - 东北大学软件学院定制
-- ============================================================

INSERT INTO `freshman_task` (`title`, `description`, `icon`, `sort_order`, `badge_level`) VALUES
('完成新生报到注册', '按照报到流程在图书馆广场完成所有注册步骤，领取校园卡', 'DocumentChecked', 10, NULL),
('参加开学典礼', '参加东北大学统一组织的开学典礼', 'Star', 20, NULL),
('完成新生军训', '在风雨操场完成新生军训任务（约2-3周）', 'Sunny', 30, 'bronze'),
('参观浑南校区图书馆', '到图书馆参观并了解借阅规则，借出第一本书', 'Reading', 40, 'bronze'),
('熟悉四大学馆', '找到信息学馆、生命学馆、文管学馆、建筑学馆的位置，了解上课教室分布', 'Location', 50, 'bronze'),
('探索浑南食堂', '尝遍食堂一楼到三楼至少5个不同窗口', 'Food', 60, NULL),
('加入一个学生组织', '选择至少一个社团或学生组织并参加活动（学生会/甲骨文俱乐部/NEX等）', 'UserFilled', 70, 'silver'),
('完成选课', '在教务系统完成本学期选课，了解培养方案和学分要求', 'Edit', 80, 'bronze'),
('参加一次"讲述软件人的故事"', '参加学院品牌活动，了解优秀学长学姐的成长经历', 'ChatRound', 90, 'silver'),
('使用图书馆自习一次', '在图书馆完成一次自习（建议体验4楼自习区）', 'Clock', 100, NULL),
('完成第一次体测', '在风雨操场完成大学生体质健康测试', 'Trophy', 110, 'silver'),
('认识3位不同学院的朋友', '主动社交，扩展跨学院朋友圈。浑南校区有10个学院共15000余人。', 'ChatLineSquare', 120, 'gold');


-- ============================================================
-- 安全防线 - 东北大学定制
-- ============================================================

INSERT INTO `safety_tip` (`title`, `content`, `sort_order`, `is_pinned`) VALUES
('防诈骗提醒：新生必读！',
 '1. 任何自称"学长/学姐"到宿舍推销电话卡、培训班、学习资料的都要警惕，不要当场付款；\n2. 不会有人打电话说"你的学费没有交"要求转账——学费统一通过学校财务系统缴纳；\n3. "兼职刷单、日结300"类信息全是诈骗，不要点击任何不明链接；\n4. 有人冒充"辅导员"或"老师"加微信要求转账的，一律先电话核实；\n5. 浑南校区公安处报警电话：024-83656110；全校校园110：024-83680110（存到手机通讯录！）。',
 0, 1),
('宿舍安全守则',
 '1. 宿舍内严禁使用大功率电器（热得快、电热毯、电磁炉等），宿管会不定期抽查，违者通报批评；\n2. 禁止在宿舍内给电动车电池充电——这是引发火灾的头号原因；\n3. 离开宿舍时关闭空调、充电器等所有电源；\n4. 不在床上吸烟，不使用明火（蜡烛、酒精炉等）；\n5. 熟悉宿舍楼消防通道位置，每层楼梯口都有灭火器和消防栓；\n6. 宿舍门禁23:00，晚归需在宿管处登记。',
 10, 1),
('浑南校区紧急电话',
 '浑南校区公安处：024-83656110\n全校校园110：024-83680110\n浑南卫生所（校医院）：024-83656263\n心理中心（浑南预约）：18804009525\n学校总值班室：024-83687388\n\n建议将这些号码存入手机通讯录并设为快捷拨号。',
 20, 1),
('冬季校园安全提醒',
 '1. 沈阳冬季气温可达-20°C，出门务必穿羽绒服+戴帽子手套；\n2. 路面结冰时小心行走，教学楼和食堂门口台阶尤其湿滑；\n3. 小南湖冬季虽然结冰但冰层厚度不足以支撑人体重量，禁止在湖面行走！\n4. 使用暖宝宝不要直接贴在皮肤上，防止低温烫伤；\n5. 宿舍暖气如有问题，联系宿管报修（不要自己拆卸）。',
 30, 0),
('实验室/机房安全',
 '1. 信息学馆各实验室和机房内禁止饮食，饮料远离设备；\n2. 离开实验室时退出所有账号、关闭电脑；\n3. 不要在实验室过夜，特殊情况需向导师报备；\n4. 发现设备异常（冒烟、异味）立即断电并报告管理员；\n5. 注意保护个人代码和实验数据，不要在公共电脑上保存密码。',
 40, 0);

SELECT '东北大学软件学院版数据库初始化完成！' AS message;
