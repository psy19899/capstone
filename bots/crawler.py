import requests 
from datetime import datetime, timedelta
from Dict import TEAM_LIST, TEAM_DICT, THIS_SEASON_TEAM_LIST, STAT_FEATURES_DICT
from bs4 import BeautifulSoup
from models.team import Team, Calendar, Member, Stat
from models.news import Post, Block
import time 
from bots.bots_extensions import create_driver
from extensions import app, db 
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import threading 
import re 
from config import Config
from AI.train import save_db_to_fs, News_Predictor, BERTClassifier
from Dict import NEWS_CATEGORY_LIST

from copy import deepcopy 

def create_teams():
    for team_name in TEAM_LIST:
        with app.app_context():
            team = Team.query.filter_by(team_name=team_name).first()
            if team is None: 
                new_team = Team(team_name=team_name)
                for catname in NEWS_CATEGORY_LIST:
                    block = Block.query.filter_by(category=catname, team_name=team_name)
                    if block is None:
                        block = Block(category=catname, team_name=team_name)
                        db.session.add(block)
                db.session.add(new_team)
                db.session.commit()

class Crawler_Players():
    def __init__(self):
        create_teams() 

    def fetch(self):
        print("[*] players crawler started")
        for team_name in TEAM_LIST:
            with app.app_context():
                team = Team.query.filter_by(team_name=team_name).first()
                if team is not None: #and not team.is_member_fetched:
                    member_info = self.get_teammember_info_from_url(team_name)

                    if member_info is not None:
                        self.commit_member_to_db(member_info)
                        #print(f"[*] {team.team_name} DB commit")
        print("[*] players crawler finished")

    """
    fetch_player helper functions
    """
    def commit_member_to_db(self, data):
        cnt = 0 
        with app.app_context():
            for dat in data:
                team = Team.query.filter_by(team_name=dat['team_name']).first()
                member = Member.query.filter_by(member_name=dat['name'], role=dat['role'], back_number=dat['back_number']).first()
                if team is not None and member is None:
                    new_member = Member(member_name=dat['name'], role=dat['role'], back_number=dat['back_number'])
                    new_member.team_id = team.id 

                    team.is_member_fetched = True 
                    
                    db.session.add(new_member)
                    try:
                        cnt += 1
                        db.session.commit()
                    except Exception as e: 
                        print(f"[-] error: {e}")
                    #print(f"[*] {dat['team_name']} DB commit")
        print("[*] players crawler db commit added {}".format(cnt))
        
    #access kleague site to get all team members' name
    def get_teammember_info_from_url(self, teamname):
        page = 1
        res = []
        team_id = TEAM_DICT[teamname]
        url = f"https://www.kleague.com/player.do?page={page}&type=active&teamId={team_id}&pos=all"
        if not self.is_team_exist(teamname):
            return None 

        tot_pages = self.get_tot_pages(url)

        while page <= tot_pages:
            url = f"https://www.kleague.com/player.do?page={page}&type=active&teamId={team_id}&pos=all"
            response = requests.get(url)

            people_soup = BeautifulSoup(response.text, 'html.parser')

            names = self.parse_player_names(teamname, people_soup)
            res.extend(names)

            page += 1
        print("[*] player crawler fetched len team {}: {}".format(teamname, len(res)))
        return res
    def is_team_exist(self, teamname):
        url = "https://www.kleague.com/player.do"
        response = requests.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')

        select = soup.find('select', id='clubList')
        if select: 
            options = select.find_all('option')

            options = [option.get_text(strip=True) for option in options]

            for option in options:
                if teamname in option:
                    return True 
        
        return False

    #helper function to get total number of pages in kleague site
    def get_tot_pages(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        li_elems = []

        ul = soup.find("ul", class_="pagination")
        if ul:
            li_elems = ul.find_all("li", class_="num")
        return len(li_elems)
    #helper function to parse the names and job name
    def parse_player_names(self, teamname, soup):
        res = []

        player_so = soup.select('div.player > div.cont-box > div.txt-box > div.txt')
        for p_div in player_so: 
            name = p_div.select_one('span[class^=name]')
            job = p_div.select_one('span[class^=num]')
            if name and job: 
                name = name.contents[0].strip() #get_text(strip=True)
                job = job.get_text(strip=True) 
                if job == '코치':
                    res.append({'name': name, 'role': job, 'back_number': None, 'team_name': teamname})
                elif 'No.' in job: 
                    back_number = int(job[3:])
                    res.append({'name': name, 'role': '선수', 'back_number': back_number, 'team_name': teamname})
                else:
                    res.append({'name': name, 'role': job, 'back_number': None, 'team_name': teamname})

        return res

class Crawler_Calendars:
    is_fetch_for_training = False 
    year_start, year_end = None, None 

    def __init__(self, for_training=False):
        create_teams()
        self.is_fetch_for_training = for_training 
        if self.is_fetch_for_training:
            self.year_start, self.year_end = 2020, 2024
        else:
            year = int(datetime.now().strftime("%Y"))
            self.year_start, self.year_end = year, year
            
    def fetch(self):
        print("[*] calendar crawler started")
        threads = []

        to_visits = []
        for year in range(self.year_start, self.year_end+1):
            off_season_months = self.get_offseasons_months_of(year)
            for month in range(12):
                if month+1 not in off_season_months:
                    date = str(year)+f"{month+1:02}"
                    to_visits.append(date)
        drivers = []

        print("[*] calendar crawling visits : {}".format(to_visits))
        print("[*] calendar crawler thread started")

        for to_visit in to_visits:
            driver = create_driver()
            thread = threading.Thread(target=self.matches_thread, args=(driver, to_visit))
            threads.append(thread)
            drivers.append(driver)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        for driver in drivers:
            driver.quit()
        
        print("[*] calendar crawler finished")

        if self.is_fetch_for_training:
            save_db_to_fs('calendar')
    """
    fetch_calendars helper functions
    """ 
            
    def get_offseasons_months_of(self, year):
        driver = create_driver()
        
        date = str(year)+'05'
        driver.get(f"https://sports.daum.net/schedule/kl?date={date}")
        time.sleep(0.2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        off_season_tags = soup.find_all('span', class_='link_day off')
        off_season_months = [int(off_season_tag['data-term']) for off_season_tag in off_season_tags]
        return off_season_months

    def matches_thread(self, driver, date):
        url = f"https://sports.daum.net/schedule/kl?date={date}"
        driver.get(url)
        
        time.sleep(0.2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        span_tags = soup.find_all('span', class_='state_game')

        if span_tags: 
            match_details = self.get_match_details(span_tags)
            self.commit_match_details_to_db(match_details)

    def commit_match_details_to_db(self, match_details):
        cnt = 0
        for match_detail in match_details:
            participants, location, data_date, reservation_url = match_detail['participants'], match_detail['location'], match_detail['data_date'], match_detail['reservation_url']
            is_past_game, target_scores, round_num = match_detail['is_past_game'], match_detail['scores'], match_detail['round_num']

            if is_past_game:
                score_A, score_B = int(target_scores[0]), int(target_scores[1])
            participant_A, participant_B = participants[0], participants[1]
            with app.app_context():
                team_A = Team.query.filter_by(team_name=participant_A).first()
                team_B = Team.query.filter_by(team_name=participant_B).first() 

            
            with app.app_context():
                schedA = Calendar.query.filter_by(match_date=data_date, opponent_team=participant_B, location=location).first()
                schedB = Calendar.query.filter_by(match_date=data_date, opponent_team=participant_A, location=location).first()
            
                if schedA is None and schedB is None:
                    new_calendar_A = Calendar(round_num=round_num, match_date=data_date, opponent_team=participant_B, location=location)
                    new_calendar_B = Calendar(round_num=round_num, match_date=data_date, opponent_team=participant_A, location=location)
                    if reservation_url is not None:
                        new_calendar_A.reservation_url=reservation_url
                        new_calendar_B.reservation_url=reservation_url
                    
                    if is_past_game:
                        new_calendar_A.this_score = score_A
                        new_calendar_A.opponent_score = score_B
                        new_calendar_B.this_score = score_B
                        new_calendar_B.opponent_score = score_A

                    new_calendar_A.is_past_game = is_past_game
                    new_calendar_B.is_past_game = is_past_game

                    if team_A and team_B:
                        new_calendar_A.team_id = team_A.id 
                        new_calendar_B.team_id = team_B.id 

                    cnt += 1
                    db.session.add(new_calendar_A)
                    db.session.add(new_calendar_B)
                elif schedA is not None and schedB is not None:
                    cur_time = datetime.now() - timedelta(hours=2)
                    if schedA.match_date < cur_time:
                        schedA.is_past_game = True 
                    if schedB.match_date < cur_time:
                        schedB.is_past_game = True 
                db.session.commit() 
                #print(f"[*] {participant_A} {participant_B} {data_date} DB commit")
        print("[*] calendar crawler db commit added len: {}".format(cnt))

    def get_match_details(self, data):
        res = []
        for span_tag in data:
            sp_txt = span_tag.get_text(strip=True)
            parent_tag = span_tag.find_parent('tr')
            is_past_game = False 
            target_scores = None 

            if '경기전' in sp_txt:
                is_past_game = False 

            elif '종료' in sp_txt:
                target_scores_tag = parent_tag.find_all('em', class_='num_score')
                target_scores = [tag.get_text(strip=True) for tag in target_scores_tag if target_scores_tag]
                is_past_game = True 
            else:
                continue

            data_date = parent_tag['data-date']
            data_time = parent_tag.find('td', class_='td_time').get_text(strip=True)
            data_date = datetime.strptime(data_date+' '+data_time, '%Y%m%d %H:%M')
            round_num = parent_tag.find('td', class_='td_tv').get_text(strip=True)[:-1]
            location_tag = parent_tag.find('td', class_='td_area')
            location = location_tag.get_text(strip=True)
            participants_tag = parent_tag.find_all('span', class_='txt_team')
            participants = [tag.get_text(strip=True) for tag in participants_tag if participants_tag]

            if round_num == '파이널 라운드':
                round_num = -2
            else:
                round_num = int(round_num)
            match_dict = {'round_num': round_num, 'data_date': data_date, 'location': location, 'participants': participants, 'is_past_game': is_past_game, 'scores': target_scores}

            reservation_url = self.get_reservation_url(match_dict)
            match_dict['reservation_url'] = reservation_url

            res.append(match_dict)
        print("[*] calendar crawler match_details len: {}".format(len(res)))
        return res 

    def get_reservation_url(self, match_dict):
        #!get reservation url of given match detail
        return None


class Crawler_Stats:
    is_fetch_for_training = False 
    year_start, year_end = None, None 
    max_attempts = 5
    particular_year = None 

    def __init__(self, for_training=False, particular_year=None):
        create_teams()
        self.is_fetch_for_training = for_training
        if not self.is_fetch_for_training and particular_year is None :
            year = int(datetime.now().strftime("%Y"))
            self.year_start, self.year_end = year, year 
        elif not self.is_fetch_for_training and particular_year is not None:
            self.year_start, self.year_end = particular_year, particular_year
        else:
            self.year_start, self.year_end = 2020, 2024
    
    def fetch(self):
        print("[*] stats crawler started")
        """
        with app.app_context():
            stat = Stat.query.filter_by(year=self.year_end).first()

        if stat is not None:
            return 
        """

        driver = create_driver()
        driver.get("https://data.kleague.com/")
        print("[*] stat crawler started ")

        start_time = time.time()
        if self.nav_to_stat_frame(driver): 
            for year in range(self.year_start, self.year_end+1):
                #!select_year
                self.select_year(driver, str(year))

                #!get_team
                each_year_teams = self.get_team_in_year(driver)
    
                threads = [] 
                driver_inners = []

                print("[*] stat crawler {} : {}".format(year, each_year_teams))
                print("[*] stat crawler thread started")
                for each_year_team in each_year_teams:
                    driver_inner = create_driver()
                    thread = threading.Thread(target=self.master_stats_thread, args=(driver_inner, year, each_year_team))
                    threads.append(thread)
                    driver_inners.append(driver_inner)

                for thread in threads:
                    thread.start()
                
                for thread in threads:
                    thread.join()

                for driver_inner in driver_inners:
                    driver_inner.quit()
                
                print("[*] stat crawler thread finished")

        end_time = time.time()
        print(f"[*] fetched stats! {(end_time-start_time):.2f} seconds")

        driver.quit()
        if self.is_fetch_for_training:
            save_db_to_fs('stats')

    def master_stats_thread(self, driver, year, team_name):
        for i in range(3):
            try:
                if self.nav_to_stat_frame(driver): 
                    self.select_year(driver, year)
                    
                    if self.nav_to_team(driver, team_name):
                        num_rounds = self.get_num_rounds(driver)
                        
                        self.reset_button(driver)
                        self.round_click(driver, 1, team_name)
                        
                        for round_num in range(num_rounds):
                            self.reset_button(driver)
                            self.round_click(driver, round_num+1, team_name)

                            for j in range(3):
                                try: 
                                    elem = driver.find_element(By.CSS_SELECTOR, 'div[class^="two-depthMenu"]')
                                    actions = ActionChains(driver)
                                    actions.move_to_element(elem).perform()
                                    time.sleep(0.2)
                                except:
                                    time.sleep(1)

                            soup = BeautifulSoup(driver.page_source, 'html.parser')

                            data = self.parse_stat_data(soup, team_name, round_num+1)
                            data['year'] = year 
                            data['round_num'] = round_num+1
                            data['tmp_team_name'] = team_name
                            
                            #print("[*] stats crawler fetched len :{}".format(len(data)))
                            
                            #print(data)
                            #print('-'*50)
                            if data['win'] is not None:
                                self.commit_stat_data(team_name, data)
            except:
                time.sleep(1)

    def nav_to_stat_frame(self, driver):
        driver.get("https://data.kleague.com/")
        driver.switch_to.frame(1)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.main-menu a')))        
        
        for i in range(3):
            try:
                to_datacenter = driver.find_element(By.CSS_SELECTOR, 'div.main-menu a')
                if to_datacenter:
                    to_datacenter.click()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.two-depthMenu')))        
                
                    to_club = driver.find_element(By.CSS_SELECTOR, 'div.two-depthMenu')
                    to_club = to_club.find_elements(By.CSS_SELECTOR, "ul > li > a")
                    a_to_club = None
                    for toto in to_club: 
                        if toto.text == '종합검색':
                            a_to_club = toto 
                            break 
                    if a_to_club:
                        a_to_club.click() 
                        #print("[*] stat crawler clicked 데이터센터")
                        return True
                return False
            except: 
                driver.get("https://data.kleague.com/")
                driver.switch_to.frame(1)
                
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.main-menu a')))        
                time.sleep(1)

    def nav_to_team(self, driver, team_name):
        """
        emble = TEAM_DICT[team_name]
        emble = f"selectTeamEmble_{emble}"
        select_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, emble)))
        if select_element:
            select_element.click()
            return True 
        return False 
        """
        for i in range(3):
            try:
                table_tag = driver.find_element(By.CSS_SELECTOR, 'table[class="total-search-table"]')
                table_tag = driver.find_elements(By.CSS_SELECTOR, 'tr > td[id^="selectTeamEmble_K"]')
                target = None 
                for tag in table_tag:
                    if team_name == tag.text:
                        target = tag 
                        break 
                if target: 
                    target.click()
                    #print("[*] stat crawler clicked team {}".format(target.text))
                    self.loading_disappear(driver)
                    return True 
                return False 
            except:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table[class="total-search-table"]')))        
                time.sleep(1)

    def select_year(self, driver, year): 
        for attempt in range(self.max_attempts):
            try:
                select = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "selectYear")))

                select = Select(select)
                select.select_by_visible_text(str(year))
                #print("[*] stat crawler clicked select year {}".format(year))
                self.loading_disappear(driver)
                break
            except:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "selectYear")))
                time.sleep(1)
                
    def round_click(self, driver, round_num, team_name):
        """
        td = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, f'total-search-bar{round_num:02}')))
        if td:
            td.click()
            
            self.loading_disappear(driver)
        """
        for attempt in range(self.max_attempts):
            try:
                table = driver.find_element(By.CSS_SELECTOR, 'table[class^="total-search-bar-data"]')
                elems = table.find_elements(By.CSS_SELECTOR, 'tr > td')
                target = None 
                for elem in elems:
                    if int(elem.text) == round_num:
                        target = elem 
                        break 
                if target: 
                    target.click()
                    #print("[*] stat crawler clicked round {} of team {}".format(target.text, team_name))
                    self.loading_disappear(driver)
                    break
            except:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table[class^="total-search-bar-data"]')))
                time.sleep(1)

    def reset_button(self, driver):
        """
        rst_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btnReset')))
        if rst_btn:
            rst_btn.click()

        """
        for attempt in range(self.max_attempts):
            try:

                rst_btn = driver.find_element(By.ID, 'btnReset')
                if rst_btn:
                    rst_btn.click()
                    #print("[*] stat crawler clicked reset button")
                    break
            except:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[id="btnReset"]')))
                time.sleep(1)

    """
    fetch_stats helper functions
    """
    def loading_disappear(self, driver):
        try:
            locator = (By.ID, 'loading_goal')
            WebDriverWait(driver, 20).until(EC.invisibility_of_element_located(locator))
        except:
            pass 
    def get_num_rounds(self, driver): 
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "total-search-bar-data"))
        )
        tds = table.find_elements(By.CSS_SELECTOR, 'tr > td')
        return len(tds)
        """
        for i in range(self.max_attempts):
            try:
                table = driver.find_element(By.CSS_SELECTOR, 'table[class^="total-search-bar-data"]')
                tds = table.find_elements(By.CSS_SELECTOR, 'tr > td')
                return len(tds)
            except:
                pass
        """
    def get_team_in_year(self, driver):
        for i in range(self.max_attempts):
            try:
                table_tag = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'table[class="total-search-table"]')))
                table_tag = table_tag.find_elements(By.CSS_SELECTOR, 'tr > td[id^="selectTeamEmble_K"]')
                return [tag.text for tag in table_tag]
            except:
                pass

    def parse_stat_data(self, soup, team_name, round_num): 
        attack_data = self.parse_stat_belonging_to(soup, label_arg='chartTeamAtt')
        pass_data = self.parse_stat_belonging_to(soup, label_arg='chartTeamPass')
        defense_data = self.parse_stat_belonging_to(soup, label_arg='chartTeamDef')
        win, opponent = self.parse_win_opponent(soup, round_num)

        pattern = r'([가-힣A-Za-z]+)\(\d+\) vs \(\d+\)([가-힣A-Za-z]+)'        
        mm = re.search(pattern, opponent)
        if mm:
            team1, team2 = mm.group(1), mm.group(2)
            if team_name == team1:
                opponent = team2 
            elif team_name == team2:
                opponent = team1
        else:
            opponent = None

        data = {}
        data.update(attack_data)
        data.update(pass_data)
        data.update(defense_data)
        data['win'] = win 
        data['opponent'] = opponent

        return data

    def parse_win_opponent(self, soup, round_num): 
        table = soup.find('table', class_="total-search-bar-data")
        span_tags = table.find_all("span")
        win, opponent = None, None
        for span in span_tags:
            if span.get_text(strip=True) == str(round_num):
                class_ = span['class'][0]
                opponent = span['title']

                if "total-search-bar01" == class_:
                    win = 'win'
                elif 'total-search-bar03' == class_:
                    win = 'draw'
                elif 'total-search-bar02' == class_:
                    win = 'lose'
                
                break 
        return (win, opponent)
    def parse_stat_belonging_to(self, soup, label_arg):
        labels = soup.select_one(f'div[id="{label_arg}"] > div > div[class^="highcharts-axis-labels"]')
        labels = labels.find_all('span', class_='total-search-chart-title')
        label_data = soup.select_one(f'div[id="{label_arg}"] > div > div[class^="highcharts-data-labels"]')
        label_data = label_data.find_all('span', class_='total-search-chart-datalabel')

        data = {}
        for i in range(len(labels)):
            target_label_x = label_data[i].get_text(strip=True)
            target_label_x_int = int(''.join([char for char in target_label_x if char.isdigit()]))
            target_label = labels[i].get_text(strip=True)
            data[STAT_FEATURES_DICT[target_label]] = target_label_x_int 
        return data 

    def commit_stat_data(self, team_name, data): 
        cnt = 0
        with app.app_context():
            team = Team.query.filter_by(team_name=team_name).first()
            stat = Stat.query.filter_by(tmp_team_name=data['tmp_team_name'], year=data['year'], round_num=data['round_num']).first()

            if stat is None:
                new_stat = Stat(**data)
                if team is not None:
                    new_stat.team_id = team.id 
                else:
                    new_stat.team_id = None

                cnt += 1
                print("[*] stat crawler added {} {} {}".format(new_stat.tmp_team_name, new_stat.year, new_stat.round_num))
                db.session.add(new_stat)
                db.session.commit()
        print("[*] stats crawler db commit added len: {}".format(cnt)) 




class Crawler_News:
    max_traversal = None 
    max_attempts = 3
    mode = None 
    dates_to_visit = [] 
    MODES = {'today': 0, 'training': 1, 'date-specific': 2, 'regular': 3}

    def __init__(self, modes='regular', dates_to_visit=None, max_traversal=Config.max_traversal):
        self.mode = self.MODES[modes]
        self.dates_to_visit = []
        self.max_traversal=max_traversal
        if dates_to_visit is not None:
            self.dates_to_visit.extend(dates_to_visit)

    def fetch(self):
        print("[*] news crawler started")
        if self.mode == self.MODES['today']:
            with app.app_context():
                post_dates = Post.query.with_entities(Post.written_date).all() 
            db_dates_list = sorted(list(set([post_date.written_date.strftime("%Y%m%d") for post_date in post_dates])))
            cur_date = datetime.now() 
            while True: 
                if cur_date.strftime("%Y%m%d") not in db_dates_list  : 
                    self.dates_to_visit.append(cur_date.strftime("%Y%m%d"))
                if cur_date.strftime("%Y%m%d") == db_dates_list[0]:
                    break 
                cur_date = cur_date - timedelta(days=1)

            self.dates_to_visit.append(datetime.now().strftime("%Y%m%d"))

        elif self.mode == self.MODES['training']:
            date = datetime.now() - timedelta(days=1)
            for i in range(30):
                self.dates_to_visit.append(date.strftime('%Y%m%d'))
                date -= timedelta(days=1)

        elif self.mode == self.MODES['date-specific']:
            #!check if self.dates_to_visit is correct format
            pass

        elif self.mode == self.MODES['regular']:
            """
            with app.app_context():
                post_dates = Post.query.with_entities(Post.written_date).all()
            db_dates_list = list(set([post_date.written_date.strftime("%Y%m%d") for post_date in post_dates]))
            """
            cnt = 0
            iter_date = datetime.now()
            while cnt < self.max_traversal:
                #if iter_date not in db_dates_list:
                self.dates_to_visit.append(iter_date.strftime("%Y%m%d"))
                cnt += 1
                iter_date = iter_date - timedelta(days=1)

        threads = []
        start_time = time.time()
        drivers = []

        print("[*] news crawler dates {}".format(self.dates_to_visit))
        print("[*] news crawler thread started")

        for iter_date in self.dates_to_visit:
            driver = create_driver()
            thread = threading.Thread(target=self.news_fetching_threads, args=(driver,iter_date))
            threads.append(thread)
            drivers.append(driver)
            print(f"[+] Thread started! {iter_date}")

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        
        for driver in drivers:
            driver.quit()
        end_time = time.time() 

        self.classifier_func()
        
        print(f"[*] Thread finished fetching articles! {end_time-start_time:.5f} seconds")

        if self.mode == self.MODES['training']:
            save_db_to_fs('news')

    #thread job to process each date
    def news_fetching_threads(self, driver, iter_date=None, dates_list=None):
        print(f"Processing {iter_date}")

        urls = self.News_get_urls_of_date(driver, iter_date)
        failed_to_visit = []
        finally_succeed = []
        if urls is not None:
            print(f"[*] {iter_date} Total number of urls : ", len(urls))
            
            if len(urls) > 0:
                news_list = []
                for url in urls:
                    news_list.append(self.News_get_contents_of_url(driver, url))
                
                print(f"[*] {iter_date} Total number of news: ", len(news_list))

                for news in news_list:
                    if news['error'] != 404 and self.commit_news_to_db(news):
                        continue 
                    failed_to_visit.append(news['url'])
                
                print("[*] news crawler failed to visit : {}".format(len(failed_to_visit)))

                trial = 0

                while len(failed_to_visit) > 0: 
                    fetched_url_list = [self.News_get_contents_of_url(driver, url) for url in failed_to_visit]
                    for fetched, prev_failed in zip(fetched_url_list, failed_to_visit):
                        if fetched['error'] != 404 and self.commit_news_to_db(fetched):
                            finally_succeed.append(prev_failed)
                            continue 
                    if trial > 3:
                        break 
                    trial += 1
        
        result = list(set(failed_to_visit)-set(finally_succeed))

        print("[*] news crawler finally failed to visit :{}| {}".format(len(result), result))
    
      #fetch data from news url
    def News_get_urls_of_date(self, driver, date):
        articles_link = []
        
        tmp_url = f"https://sports.news.naver.com/kfootball/news/index?isphoto=N"
        
        for i in range(3):
            try: 
                driver.get(tmp_url)

                self.click_kleague_button(driver)
                self.nav_to_date(driver, date)

                pages = self.get_anchor_tags_of_page(driver)
                articles_link.extend(pages) 

                time.sleep(0.1)

                pag = driver.find_element(By.ID, '_pageList')
                pag_a_tags = pag.find_elements(By.TAG_NAME, 'a')
                pag_a_tags = [tag for tag in pag_a_tags if tag.text.isdigit()]
                len_a_tags = len(pag_a_tags)
                to_visit = 2

                if len_a_tags >= 1:
                    for i in range(len_a_tags):
                        for j in range(3):
                            try:
                                pag = driver.find_element(By.ID, '_pageList')
                                pag_a_tag = pag.find_element(By.XPATH, f'//a[@data-id="{to_visit}"]')
                                
                                pag_a_tag.click() 
                                #print(f"page {pag_a_tag.text} clicked")
                                
                                pages = self.get_anchor_tags_of_page(driver)
                                articles_link.extend(pages)    

                                to_visit += 1   
                            except: 
                                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "_pageList")))
                                time.sleep(1)  
            except: 
                time.sleep(1)
        
        with app.app_context():
            posts = Post.query.all()
            filtered_link = set([post.url for post in posts])

            articles_link = [article for article in articles_link if article not in filtered_link]

            return articles_link

    def News_get_contents_of_url(self, driver, url):
        res = {}

        max_retries = 3
        for i in range(max_retries):
            try:
                driver.get(url) 
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'content')))
                tmp = driver.find_element(By.CSS_SELECTOR, "h2[class^='NewsEndMain_article_title']") 

                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, "h2[class^='NewsEndMain_article_title']")
                    title = title_element.text.strip()
                except NoSuchElementException:
                    title = None

                try:
                    content_div = driver.find_element(By.CSS_SELECTOR, "article[class^='NewsEndMain_comp_news_article__']")
                    try:
                        article_div = content_div.find_element(By.CSS_SELECTOR, "div[class^='_article_content']")
                        
                        try:
                            video = article_div.find_element(By.CSS_SELECTOR, "div[class*='NewsEndMain_comp_article_video']")
                            driver.execute_script("arguments[0].remove();", video)
                        except NoSuchElementException:
                            pass 

                        content = article_div.text.strip().replace('\n', ' ')
                    except NoSuchElementException:
                        content = "No div"
                except NoSuchElementException:
                    content = None

                try:
                    reporter_name_element = driver.find_element(By.CSS_SELECTOR, "span[class^='NewsEndMain_author__']")
                    reporter_name = reporter_name_element.text.strip()
                except NoSuchElementException:
                    reporter_name = None

                try:
                    written_date_element = driver.find_element(By.CSS_SELECTOR, "em[class^='NewsEndMain_date__']")
                    written_date = datetime.strptime(written_date_element.text.strip()[:11], "%Y.%m.%d.")
                except NoSuchElementException:
                    written_date = None
                team = None
                category = None 
                #print("[*] news crawler parsed content of url : {}".format(title[:20]))
                res = {'error': 200, "headline": title, 'category': category, 'contents': content, 'author': reporter_name, 'written_date': written_date, 'url': url, 'team': team}
                
                return res
                break 
            except: 
                #print("[*] news crawler retrying get_contents")
                if i == max_retries-1:
                    res = {"error": 404, "url": url}
                    return res 
                time.sleep(1)
        
        
    
    def get_anchor_tags_of_page(self, driver):
        res = []
        
        for i in range(3):
            try: 
                news_list = driver.find_element(By.ID, "_newsList")
                news_list = news_list.find_elements(By.CSS_SELECTOR, 'ul > li > a')
        
                res = [a_tag.get_attribute('href') for a_tag in news_list if a_tag]
                return res
            except:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "_newsList")))
                time.sleep(1)

    #helper function to click kleague buttn in naver.news (naver news uses dynamic loading)
    def click_kleague_button(self, driver):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, '_sectionList')))
        for i in range(3):
            try:
                kli = driver.find_element(By.ID, '_sectionList')

                kli = kli.find_element(By.CSS_SELECTOR, 'li[data-id^="kleague"]')

                kli = kli.find_element(By.TAG_NAME, 'a')
                if kli:
                    print(kli.tag_name, kli.text, 'clicked')
                    #print("-"*50)
                    kli.click()
                    #driver.execute_script("arguments[0].click();", kli)
            except: 
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, '_sectionList')))
                time.sleep(1)

    #helper function to click date button in naver.news (naver news uses dynamic loading)
    def nav_to_date(self, driver, date):
        #assume kleague button is pressed

        for i in range(3):
            try: 
                found = False
                while not found:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, '_bottomDateList')))
                    time.sleep(0.1)

                    div_pag = driver.find_element(By.ID, "_bottomDateList")

                    #WebDriverWait(div_pag, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.inner')))
                    if div_pag:
                        WebDriverWait(div_pag, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.inner > a')))

                        inner_a = div_pag.find_elements(By.CSS_SELECTOR, "div.inner > a")

                        """
                        for all_ in inner_a:
                            print(all_.tag_name, all_.text)
                        print('-'*50)
                        """

                        for a_tag in inner_a: 
                            if a_tag.get_attribute('data-id') == date:
                                print(a_tag.tag_name, a_tag.text, 'clicked')
                                a_tag.click()
                                found = True 
                                break 
                        if found:
                            break 
                        else:
                            dt_btn = div_pag.find_element(By.CSS_SELECTOR, 'a[class^="prev"]')
                            if dt_btn:
                                dt_btn.click()
            except: 
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, '_bottomDateList')))
                time.sleep(1)

    def classifier_func(self):
        with app.app_context():
            for team_name in THIS_SEASON_TEAM_LIST: 
                for cat_name in NEWS_CATEGORY_LIST: 
                    block = Block.query.filter_by(category=cat_name, team_name=team_name).first()
                    if block == None: 
                        block = Block(category=cat_name, team_name=team_name)
                        db.session.add(block)
            db.session.commit()


            posts = Post.query.all() 
            post_cat_none = [post for post in posts if post.category==None]
            
            headlines = [post.headline for post in post_cat_none]
            
            predictions = News_Predictor().predict(headlines)
            
            print("[*] news crawler classifying {}".format(len(predictions)))

            for prediction, post in zip(predictions, post_cat_none): 
                sentence, label = prediction[0], prediction[1] 
                post.category = label
                #print(f"[*] {label} : {sentence}")
                #print(f"[*] {post.headline}")
                #print("-"*50)
            db.session.commit()
            

            posts = Post.query.all() 
            post_team_none = [post for post in posts if post.team==None]
            print("[*] news crawler classifying into teams")

            for post in post_team_none:
                team = self.News_classify_articles_into_team(post)
                if len(team) == 1: 
                    post.team = team[0]
                elif len(team) > 1:
                    """
                    post_bck = Post_Bck(headline=post.headline, contents=post.contents, url=post.url, author=post.author, written_date=post.written_date)
                    db.session.add(post_bck)
                    """

                    db.session.delete(post) 
                    for team_name in team: 
                        post_tmp = Post(headline=post.headline, contents=post.contents, url=post.url, author=post.author, written_date=post.written_date, team=team_name, category=post.category)
                        db.session.add(post_tmp) 
            db.session.commit()


            posts = Post.query.all()
            posts = [post for post in posts if post.block_id==None and post.team is not None]
            for post in posts: 
                block = Block.query.filter_by(category=post.category, team_name=post.team).first()
                if block is not None:
                    post.block_id = block.id
            db.session.commit()

    #helper function to classify articles
    def News_classify_articles_into_team(self, post):
        title = post.headline 
        contents = post.contents 
        """
        if bool(re.match('\b[kK]\s*리그\s*([12])?\b', title)):
            return THIS_SEASON_TEAM_LIST
        """

        #!improve algorithm for classification
        res = [] 
        with app.app_context():
            for team_name in THIS_SEASON_TEAM_LIST:
                db_member_names = self.get_member_names_of_team_in_db(team_name)
                if title and team_name in title and team_name not in res:
                    res.append(team_name)
                    #print(title, team_name)
                if contents and team_name in contents and team_name not in res:
                    res.append(team_name)

                for member_name in db_member_names:
                    if title and member_name in title and team_name not in res:
                        res.append(team_name)
                        #print(title, member_name)
                    if contents and member_name in contents and team_name not in res: 
                        res.append(team_name)
        return res
    

    def get_member_names_of_team_in_db(self, team_name):
        with app.app_context():
            team = Team.query.filter_by(team_name=team_name).first() 
            members = team.members
            member_names = list(set([member.member_name for member in members]))
            return member_names
    #put news data into db
    def commit_news_to_db(self, data):
        cnt = 0
        with app.app_context():
            past_post = Post.query.filter_by(headline=data['headline']).first()
    
            if past_post is None:
                #for team in data['team']:
                post = Post(headline=data['headline'], category=data['category'], contents=data['contents'], author=data['author'], url=data['url'], written_date=data['written_date'], team=data['team'])

                db.session.add(post)
                try:
                    #print(f"[*] {post.headline} DB session commit!")
                    db.session.commit()
                    cnt += 1
                    return True
                except Exception as e:
                    print("[-] DB session failed")
                    db.session.rollback()
                finally:
                    db.session.remove()
            return False
        print("[*] news crawler committed into db : {}".format(cnt))
    #helper function to parse url a tags in <naver news>