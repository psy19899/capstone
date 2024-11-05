from extensions import db, app
from models.news import Post, ClusterCenter
from models.team import Team
from Dict import TEAM_LIST
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Normalizer
import numpy as np 


from collections import defaultdict


def Cluster_articles(data):
    if data is None: #create new clusters
        initial_grouping('서울')

    else: #assign to existing cluster
        pass
        cluster_centers = load_cluster_object_from_db()
        assign_closest_center(cluster_centers, data['contents'])

def initial_grouping(team_name):
    prune_duplicate_posts(team_name)
    #clusters = second_clustering(team_name)

    #save_cluster_object_to_db(clusters)

br = lambda : print("-"*30)
def second_clustering(team_name):
    posts = get_posts_from_db(team_name)
    article_contents = [post.headline for post in posts]

    vt = TfidfVectorizer()
    tf_matrix = vt.fit_transform(article_contents)

    dbscan = DBSCAN(eps=0.1, min_samples=2, metric='cosine')
    clusters = dbscan.fit_predict(tf_matrix)
    
    clustered_articles = defaultdict(list)
    for cluster_id, content in zip(clusters, article_contents):
        clustered_articles[cluster_id].append(content)
    
    for cluster_id, contents in clustered_articles.items():
        print(f"cluster {cluster_id}")
        for content in contents: 
            print(f"- {content}")
        br()
    return clusters 

def load_cluster_object_from_db():
    with db.app.app_context():
        cluster_centers = {}
        centers = ClusterCenter.query.all()
        for center in centers:
            cluster_centers[center.cluster_label] = center.center_vector
        return cluster_centers
def save_cluster_object_to_db(clusters):
    cluster_centers = {}
    for cluster_label in set(clusters):
        if cluster_label != -1: 
            idxs = np.where(clusters == cluster_label)[0]
            center_vector = tf_matrix[idxs].mean(axis=0)
            cluster_centers[cluster_label] = center_vector

    with db.app.app_context():
        for cluster_label, center_vector in cluster_centers.items():
            cluster_center = ClusterCenter(cluster_label=cluster_label, center_vector=center_vector)
            db.session.add(cluster_center)
        db.session.commit()
def get_posts_from_db(team_name):
    with app.app_context():
        posts = Post.query.filter_by(team=team_name).all() 
    return posts
def prune_duplicate_posts(team_name):
    posts = get_posts_from_db(team_name)
    article_contents = [post.headline for post in posts]

    vt = TfidfVectorizer(analyzer='word', min_df = 1, ngram_range=(1,3))
    tf_matrix = vt.fit_transform(article_contents)


    dbscan = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
    clusters = dbscan.fit_predict(tf_matrix)

    clustered_articles = defaultdict(list)
    for cluster_id, content in zip(clusters, article_contents):
        clustered_articles[cluster_id].append(content)

    refined_clustered_articles = defaultdict(str)
    for cluster_id, contents in clustered_articles.items():
        #refined_clustered_articles[cluster_id] = contents[0]
        print(f"cluster {cluster_id}")
        for content in contents: 
            print(f"- {content}")
        br()
        """
        if len(contents) > 1:
            for i in range(1, len(contents)):
                post = Post.query.filter_by(contents=contents[i]).first()
                db.session.delete(post)
            
            db.session.commit()
        """

def assign_closest_center(cluster_centers, article):
    new_article_vector = vectorizer.transform([article])
        
    distances = []
    for cluster_label, center_vector in cluster_centers.items():
        distance = 1 - (new_article_vector @ center_vector.T).A[0][0]
        distances.append((cluster_label, distance))

    closest_cluster_label = min(distances, key=lambda x: x[1])[0]

    with db.app.app_context():
        new_post = Post(contents=new_article_content, cluster_label=closest_cluster_label)
        db.session.add(new_post)
        db.session.commit()