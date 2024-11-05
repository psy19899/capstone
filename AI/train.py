from extensions import db, app 
from models.team import Team, Stat 
from models.news import Post 
from Dict import STAT_FEATURES_training
import csv 
import joblib
import os 
import numpy as np 
import pandas as pd
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

import torch
from torch import nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import gluonnlp as nlp
import numpy as np
from tqdm import tqdm, tqdm_notebook
from kobert_tokenizer import KoBERTTokenizer
from transformers import BertModel

class BERTDataset(Dataset):
    def __init__(self, dataset, sent_idx, label_idx, bert_tokenizer, vocab, max_len,
                 pad, pair):
        transform = nlp.data.BERTSentenceTransform(
            bert_tokenizer, max_seq_length=max_len, vocab=vocab, pad=pad, pair=pair)

        self.sentences = [transform([i[sent_idx]]) for i in dataset]
        self.labels = [np.int32(i[label_idx]) for i in dataset]

    def __getitem__(self, i):
        return (self.sentences[i] + (self.labels[i], ))

    def __len__(self):
        return (len(self.labels))


class BERTClassifier(nn.Module):
    def __init__(self,
                 bert,
                 hidden_size = 768,
                 num_classes=9,
                 dr_rate=None,
                 params=None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate

        self.classifier = nn.Linear(hidden_size , num_classes)
        if dr_rate:
            self.dropout = nn.Dropout(p=dr_rate)

    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)

        _, pooler = self.bert(input_ids = token_ids, token_type_ids = segment_ids.long(), attention_mask = attention_mask.float().to(token_ids.device))
        if self.dr_rate:
            out = self.dropout(pooler)
        return self.classifier(out)

class News_Predictor: 
    device = None 
    model = None 
    tokenizer = None 
    tok = None 
    vocab = None 
    max_len = 64
    batch_size = 64

    def __init__(self):
        fileabs = os.path.abspath(__file__)
        self.path = os.path.dirname(fileabs)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = torch.load(self.path+"/model.pt", map_location=self.device)
        self.tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
        self.tok = self.tokenizer.tokenize
        self.vocab = nlp.vocab.BERTVocab.from_sentencepiece(self.tokenizer.vocab_file, padding_token='[PAD]')
        #self.bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)

    def predict(self, target_sentence):
        dataset = [[sentence, '0'] for sentence in target_sentence]

        testset = BERTDataset(dataset, 0, 1, self.tok, self.vocab, self.max_len, True, False)
        dataloader = torch.utils.data.DataLoader(testset, batch_size=self.batch_size, num_workers=5)

        self.model.eval()
        test_eval = []

        for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(dataloader):
            token_ids = token_ids.long().to(self.device)
            segment_ids = segment_ids.long().to(self.device)

            valid_length= valid_length
            label = label.long().to(self.device)

            out = self.model(token_ids, valid_length, segment_ids)

            for i in out:
                logits=i
                logits = logits.detach().cpu().numpy()

                if np.argmax(logits) == 0:
                    test_eval.append("interview")
                elif np.argmax(logits) == 1:
                    test_eval.append("match_result")
                elif np.argmax(logits) == 2:
                    test_eval.append("match_plan")
                elif np.argmax(logits) == 3:
                    test_eval.append("club_internal")
                elif np.argmax(logits) == 4:
                    test_eval.append("player_idv")
                elif np.argmax(logits) == 5:
                    test_eval.append("issue")
                elif np.argmax(logits) == 6:
                    test_eval.append("trade")
                elif np.argmax(logits) == 7:
                    test_eval.append("squad")
        res = []
        for sentence, prediction in zip(target_sentence, test_eval):
            res.append([sentence, prediction])
        return res 
        
    
class Stat_Predictor:
    model = None 
    team_A, team_B = None, None 
    stat_AB = None 
    path = None 
    LABEL = {'0': 'draw', '1': 'lose', '2': 'win'}

    def __init__(self, team_A, team_B):
        self.team_A = team_A
        self.team_B = team_B
        self.path = os.path.dirname(os.path.realpath(__file__))
    
    def predict(self):
        if self.load_model() and self.load_data():
            prediction = self.model.predict(self.stat_AB)
            #probab = self.model.predict_proba(self.stat_AB)
            label = self.LABEL[str(prediction[0])]
            return label

    def train(self):
        train_df = pd.read_csv(self.path + "stats.csv")

        other_df = train_df.copy()
        columns_exclude = ["year", "round_num", "tmp_team_name", "opponent", "win"]
        other_df2 = other_df.drop(columns=columns_exclude)
        other_df2.columns = [f"{col}_opponent" for col in other_df2.columns]
        other_df2.loc[:, :] = -1

        df = pd.concat([train_df, other_df2], axis=1)

        stat_features = ['goals', 'assists', 'total_shootings', 'shots_on_target', 'shots_blocked', 'shots_out_of_bounds', 'shots_in_PA', 'shots_out_PA', 'offsides', 'freekicks_on_target', 'freekicks_on_cross', 'cornerkicks', 'throwins', 'dribbles', 'tot_passes', 'passes_critical', 'passes_in_defense_area', 'passes_long_range', 'passes_short_range', 'passes_forward', 'passes_middle_range', 'passes_horizontal', 'passes_backward', 'passes_crosses', 'passes_in_attack_area', 'passes_in_middle_area', 'dismarks', 'tackles', 'fights_air', 'fights_ground', 'ball_intercepts', 'ball_clearings', 'ball_cuts', 'ball_gains', 'ball_blocks', 'ball_misses', 'fouls_against_other_team', 'fouls_against_own_team', 'yellow_cards', 'red_cards', 'goals_conceded', 'goalkeeper_catchings', 'goalkeeper_punchings', 'goalkeeper_goalkicks', 'goalkeeper_air_clearings']

        to_drop = []
        for i, this_team in df.iterrows():
            if i in to_drop:
                continue
            opponent = df[(df['year'] == this_team.year) & (df['round_num'] == this_team.round_num) & (df['tmp_team_name'] == this_team.opponent) & (df['opponent'] == this_team.tmp_team_name)]

            if not opponent.empty:
                for feature in stat_features:
                    df.at[i, feature + '_opponent'] = opponent[feature].values[0]
                    to_drop.extend(opponent.index.tolist())

        df.drop(index=to_drop, inplace=True)

        df = df[df.goals_opponent != -1]

        labels = df['win']
        exclude_columns = ['win', 'year', 'round_num', 'tmp_team_name', 'opponent', 'dismarks', 'goals', 'goals_opponent', 'goals_conceded', 'goals_conceded_opponent']

        df = df.drop(columns=exclude_columns)
        data = df.dropna(axis=1, how='any')
        data_tmp = pd.concat([data, labels], axis=1)

        label_encoder = LabelEncoder()

        labels = label_encoder.fit_transform(labels)
        X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

        model = SVC(kernel='linear')
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        print("Accuracy:", accuracy_score(y_test, y_pred))
        print(classification_report(y_test, y_pred))

        joblib.dump(model, self.path+'stats_model.pkl')
        
    def load_model(self):
        try:
            self.model = joblib.load(self.path+'/stats_model.pkl')
            return True 
        except:
            return False 
    def load_data(self):
        with app.app_context():
            team_A = Team.query.filter_by(team_name=self.team_A).first()
            team_B = Team.query.filter_by(team_name=self.team_B).first()

            if team_A is not None and team_B is not None:
                stat_A = sorted(team_A.stats, key=lambda team: (team.year, team.round_num), reverse=True)[0]
                stat_B = sorted(team_B.stats, key=lambda team: (team.year, team.round_num), reverse=True)[0]

                self.stat_AB = np.array(stat_A.to_list() + stat_B.to_list()).reshape(1,-1)
                return True 
            return False 

#saving collected stat data from db to csv file
def save_db_to_fs(caller):
    is_exist = False 
    if caller == 'news':
        news = Post.query.all() 
        data = [] 
        for it in news: 
            data.append({'headline': it.headline, 'contents': it.contents, 'url': it.url, 'author': it.author, 'date': it.written_date})
        colnames = data[0].keys() 

        is_exist = True 
    elif caller == 'stats':
        with app.app_context():
            stats = Stat.query.all()

            data = [] 
            for stat in stats:
                if stat.win is not None:
                    data.append(stat.to_dict())
                    print(f"{stat.year} {stat.round_num} {stat.tmp_team_name} {stat.goals} added")
                    print("-"*50)
            
            colnames = data[0].keys()
            is_exist = True 
    if is_exist:
        with open(f"{caller}.csv", mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=colnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"[*] {caller}.csv saved to fs")