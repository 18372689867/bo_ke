from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from tools.login_dec import login_check
import json
from .models import Topic

from user.models import UserProfile
from tools.login_dec import get_user_by_request

from message.models import Message

from tools.cache_dec import topic_cache
from django.core.cache import cache


class TopicView(View):

    # 清除缓存的方法
    def clear_topic_caches(self, request):
        # 准备6种不同的key，删除操作[15分钟]，16:30回来带着写
        # 1. 前缀是用来区分权限的
        part1 = ['topic_cache_self_', 'topic_cache_']
        # 2. 中间部分是path    request.path_info
        part2 = request.path_info
        # 3. 后缀用来区分分类的['','?category=tec','?category=no-tec']
        part3 = ['', '?category=tec', '?category=no-tec']
        # 4. 三部分组合到一起，添加一个key的列表中
        all_keys = []
        for p1 in part1:
            for p3 in part3:
                all_keys.append(p1 + part2 + p3)
        print(all_keys)
        # 5. 删除keys     cache.delete_many()
        cache.delete_many(all_keys)

    @method_decorator(login_check)
    def post(self, request, author_id):
        # 1 从请求对象的附加数据中获取用户对象
        author = request.myuser
        # 2 从前端获取用户输入的值(内容，不带格式的内容，权限，分类，标题)
        json_str = request.body
        json_obj = json.loads(json_str)
        content = json_obj['content']
        content_text = json_obj['content_text']
        introduce = content_text[:20]
        title = json_obj['title']
        # 3 检查分类的值一定是tec 或no-tec
        #   检查权限的值一定是public或private
        category = json_obj['category']
        if category not in ['tec', 'no-tec']:
            result = {'code': 10300, 'error': '分类错误！'}
            return JsonResponse(result)
        limit = json_obj['limit']
        if limit not in ['public', 'private']:
            result = {'code': 10301, 'error': '权限错误！'}
            return JsonResponse(result)
        # 5数据入库  （查表topic中是否有新添加的信息）
        Topic.objects.create(title=title, content=content,
                             limit=limit, category=category,
                             introduce=introduce,
                             user_profile=author)

        # 如果对文章列表使用了缓存，清缓存
        self.clear_topic_caches(request)
        # 6 返回
        return JsonResponse({'code': 200,
                             'username': author.username})

    @method_decorator(topic_cache(100))
    def get(self, request, author_id):
        print('---topic get view in------')
        # 增加文章详情页功能时， v1/topics/aid2010?tid=2
        # 所以有无tid这个查询字符串，就是详情页和列表页区别的条件

        # 1. 分类的思考
        # v1/topics/aid2010   # 所有的分类
        # v1/topics/aid2010?category=tec|no-tec  # 技术或非技术文章列表

        # 2. 权限的思考
        # 登录用户访问自己的文章，可以访问所有文章(包括public+private)
        # 游客、登录用户访问别人的文章，只能访问 public文章。
        # 区分开访问者是不是作者本人

        # 1 获取文章的作者这个对象
        try:
            author = UserProfile.objects.get(username=author_id)
        except:
            result = {'code': 10305, 'error': '用户名称错误！'}
            return JsonResponse(result)

        # 2 获取访问者的姓名（有可能是游客，有可能是某一登录用户）
        visitor_name = get_user_by_request(request)

        # 增加文章详情页的操作
        t_id = request.GET.get('t_id')
        is_self = False
        # 文章详情页【】
        if t_id:
            # 博主访问自己
            if visitor_name == author_id:
                is_self = True
                try:
                    author_topic = Topic.objects.get(id=t_id,
                                                     user_profile_id=author_id)
                except:
                    result = {'code': 10310, 'error': 'topic id is error'}
                    return JsonResponse(result)

            # 非博主访问，增加过滤条件 limit='public'
            else:
                try:
                    author_topic = Topic.objects.get(id=t_id,
                                                     user_profile_id=author_id,
                                                     limit='public')
                except:
                    result = {'code': 10310, 'error': 'topic id is error'}
                    return JsonResponse(result)
            # 构造返回值的json格式
            res = self.make_topic_res(author, author_topic, is_self)
            return JsonResponse(res)
        # 文章列表页
        else:
            # 3 分类的操作
            fiter_category = False
            category = request.GET.get('category')
            if category in ['tec', 'no-tec']:
                fiter_category = True

            # 根据分类和权限，编写四种不同的查询条件

            # 博主访问自己，无需增加权限过滤
            if visitor_name == author_id:
                # 需要增加分类过滤，category=category
                if fiter_category:
                    author_topics = Topic.objects.filter(user_profile_id=author_id,
                                                         category=category)
                # 无需分类
                else:
                    author_topics = Topic.objects.filter(user_profile_id=author_id)
            # 博主访问自己，增加权限过滤 limit = ‘public’
            else:
                # 需要增加分类过滤，category=category
                if fiter_category:
                    author_topics = Topic.objects.filter(user_profile_id=author_id,
                                                         category=category,
                                                         limit='public')
                # 无需分类
                else:
                    author_topics = Topic.objects.filter(user_profile_id=author_id,
                                                         limit='public')
            # 根据传入的参数：作者、文章列表，构建一个前端要求的Json格式的返回值
            res = self.make_topics_res(author, author_topics)
            return JsonResponse(res)

    def make_topic_res(self, author, author_topic, is_self):
        # 生成详情页的返回值
        result = {'code': 200, 'data': {}}
        # 1 文章详情数据
        result['data']['nickname'] = author.nickname
        result['data']['title'] = author_topic.title
        result['data']['category'] = author_topic.category
        result['data']['content'] = author_topic.content
        result['data']['introduce'] = author_topic.introduce
        result['data']['author'] = author.nickname
        result['data']['created_time'] = author_topic.created_time.strftime('%Y-%m-%d %H:%M:%S')
        # 2 文章表中上一篇下一篇
        if is_self:
            next_topic = Topic.objects.filter(id__gt=author_topic.id,
                                              user_profile_id=author.username).first()
            last_topic = Topic.objects.filter(id__lt=author_topic.id,
                                              user_profile_id=author.username).last()
        else:
            next_topic = Topic.objects.filter(id__gt=author_topic.id,
                                              user_profile_id=author.username,
                                              limit='public').first()
            last_topic = Topic.objects.filter(id__lt=author_topic.id,
                                              user_profile_id=author.username,
                                              limit='public').last()
        if next_topic:
            next_id = next_topic.id
            next_title = next_topic.title
        else:
            next_id = None
            next_title = None

        if last_topic:
            last_id = last_topic.id,
            last_title = last_topic.title
        else:
            last_id = None
            last_title = None

        result['data']['last_id'] = last_id
        result['data']['last_title'] = last_title
        result['data']['next_id'] = next_id
        result['data']['next_title'] = next_title

        # 3 与评论表相关数据
        # 3.1 从数据表中获取所有的评论和回复
        all_messages = Message.objects.filter(topic=author_topic).order_by('-created_time')

        msg_list = []

        # 回复的信息
        r_dict = {}
        # 统计评论的数量
        msg_count = 0

        for msg in all_messages:
            if msg.parent_message:
                # 回复
                r_dict.setdefault(msg.parent_message, [])
                r_dict[msg.parent_message].append({
                    'msg_id': msg.id,
                    'content': msg.content,
                    'publisher': msg.user_profile.nickname,
                    'publisher_avatar': str(msg.user_profile.avatar),
                    'created_time': msg.created_time.strftime('%Y-%m-%d %H:%M:%S')})

            else:
                # 评论
                msg_count += 1
                msg_list.append({
                    'id': msg.id,
                    'content': msg.content,
                    'publisher': msg.user_profile.nickname,
                    'publisher_avatar': str(msg.user_profile.avatar),
                    'created_time': msg.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'reply': []})

        # 将回复与评论关联
        for m in msg_list:
            if m['id'] in r_dict:
                m['reply'] = r_dict[m['id']]

        result['data']['messages'] = msg_list
        result['data']['messages_count'] = msg_count
        return result

    def make_topics_res(self, author, author_topics):
        topics_res = []

        for topic in author_topics:
            d = {}
            d['id'] = topic.id
            d['title'] = topic.title
            d['category'] = topic.category
            d['introduce'] = topic.introduce
            d['created_time'] = topic.created_time.strftime('%Y-%m-%d %H:%M:%S')
            d['author'] = author.nickname
            topics_res.append(d)

        res = {'code': 200, 'data': {}}
        res['data']['topics'] = topics_res
        res['data']['nickname'] = author.nickname
        return res
