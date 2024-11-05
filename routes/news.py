from flask import jsonify, request, Blueprint
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.news import Block, Post
from models.users import User
from Dict import NEWS_CATEGORY_LIST
import re 
from datetime import datetime 

news_route = Blueprint('news', __name__)

@news_route.route("/api/news/all_blocks", methods=['GET'])
@jwt_required() 
def all_blocks():
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({"msg": 'something wnet wrong'})
    
    posts = Post.query.filter_by(team=user.team).all()

    if posts is None: 
        return jsonify({"msg": "no posts found yet"})
    return jsonify([post.to_dict() for post in posts])

@news_route.route("/api/news/category_names", methods=['GET'])
def features():
    return jsonify(NEWS_CATEGORY_LIST)

@news_route.route("/api/news/block_headlines", defaults={"category": None}, methods=['GET'])
@news_route.route("/api/news/block_headlines/<category>", methods=['GET'])
@jwt_required()
def block_headlines(category):
    #returns headlines of all the blocks
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({"msg": 'something wnet wrong'})
    
        
    if category is not None:    
        if category not in NEWS_CATEGORY_LIST: 
            return jsonify(NEWS_CATEGORY_LIST)
    
        block = Block.query.filter_by(team_name=user.team, category=category).first()
        if block is None: 
            return jsonify({"msg": "no articles found"})
        
        headlines = [post.headline for post in block.posts]

        return jsonify(headlines)
    
    posts = Post.query.filter_by(team=user.team).all()
    res = [post.headline for post in posts] 
    return jsonify(res)

@news_route.route("/api/news/block_internal", defaults={"category": None, "date": None}, methods=['GET'])
@news_route.route("/api/news/block_internal/<category>", defaults={"date": None}, methods=['GET'])
@news_route.route("/api/news/block_internal/<category>/<date>", methods=['GET'])
@jwt_required()
def block_internal(category, date):
    #returns headlines and url of the news article related to the block.
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({"msg": 'something wnet wrong'})
    
    if category is not None:
        if category not in NEWS_CATEGORY_LIST:
            return jsonify(NEWS_CATEGORY_LIST)
        block = Block.query.filter_by(team_name=user.team, category=category).first()
        if block is None:
            return jsonify({"msg": "no articles found"})
        posts = block.posts 

        res = []
        if date is None:
            res = [post.to_dict() for post in posts]
        else: 
            try:
                date = datetime.strptime(date, '%Y%m%d')
                res = [post.to_dict() for post in posts if post.written_date == date]
            except:
                return jsonify({"msg": "date must be %Y%m%d (ex. 19990125)"})
        
        if len(res) == 0: 
            return jsonify({"msg": "no articles found"})
        return jsonify(res)

    posts = Post.query.filter_by(team=user.team).all()
    if posts is None: 
        return jsonify({'msg': "no articles found"})
    res = [post.to_dict() for post in posts] 
    return jsonify(res) 
    
@news_route.route("/api/news/keywords", methods=['GET'])
@jwt_required() 
def news_keywords():
    pass 

@news_route.route("/api/news/comments", methods=['GET', 'POST'])
@jwt_required()
def news_comments():
    if request.method == 'GET':
        #returns comments of the users of the block 
        pass
    if request.method== 'POST':
        #push the comment written by user to the db 
        pass 

@news_route.route("/api/news/comments", methods=['DELETE'])
@jwt_required()
def comments_delete():
    #delete user comments
    pass
    
@news_route.route("/api/news/comments", methods=['UPDATE'])
@jwt_required()
def comments_update():
    #delete user comments
    pass