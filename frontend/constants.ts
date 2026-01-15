import { User } from './types';

export const MOCK_USERS: User[] = [
  {
    id: '1',
    name: '王女士',
    tier: 'VVIP',
    score: 98,
    recentStore: '上海恒隆广场店',
    lastVisit: '3天前',
    reason: '上月到访上海恒隆店3次 + 点击新品邮件'
  },
  {
    id: '2',
    name: '陈小姐',
    tier: 'VIP',
    score: 95,
    recentStore: '北京SKP',
    lastVisit: '1周前',
    reason: '过去90天购买过2件配饰 + 浏览手袋页面超过10次'
  },
  {
    id: '3',
    name: '李先生',
    tier: 'VVIP',
    score: 92,
    recentStore: '成都IFS',
    lastVisit: '2周前',
    reason: '年度消费总额 Top 5% + 情人节礼品搜索记录'
  },
  {
    id: '4',
    name: '张女士',
    tier: 'Member',
    score: 88,
    recentStore: '深圳湾万象城',
    lastVisit: '5天前',
    reason: '近期升级为金卡会员 + 收藏了春季新款'
  },
  {
    id: '5',
    name: '刘小姐',
    tier: 'VIP',
    score: 85,
    recentStore: '杭州大厦',
    lastVisit: '1个月前',
    reason: '高频浏览度假系列 + 曾购买过同品牌小皮具'
  }
];

export const INITIAL_PROMPT = "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。";

export const AVG_ORDER_VALUE = 18000; // CNY