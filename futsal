import httpx
from bs4 import BeautifulSoup #knihovna pro parsovani html stranky

hlavni_url = 'https://futsalvplzni.cz'
url = 'https://futsalvplzni.cz/tymy-statistiky'
link_hotovo = " .link-secondary[href]"
class PlayerPageInfo:
    def __init__(self, id:str,name: str, url: str, goals: int, assists: int, yellow_cards: int, red_cards: int, matches_played: int, team:str,league:str):  
        self.id = id
        self.name = name
        self.url = url
        self.goals = goals
        self.assists = assists
        self.yellow_cards = yellow_cards
        self.red_cards = red_cards
        self.matches_played = matches_played
        self.team = team
        self.league = league
    def __hash__(self):
        return hash((self.id)) 
    def __eq__(self, other):
        if isinstance(other, PlayerPageInfo):
            return (self.id) == (other.id)
        
class TeamPageInfo: 
    def __init__(self, name: str ,url: str):
        self.name = name
        self.url = url
        self.players = set()
        
    def add_players(self,player: PlayerPageInfo):
        self.players.add(player)
    @property
    def number_of_players(self):
        return len(self.players)

class FVPCrawler:

    link = ".link-secondary[href]"


    
    def __init__(self,hlavni_url:str, url:str, link_hotovo:str):
        self.tymy:dict[str] = {}
        self.hlavni_url = hlavni_url
        self.url = url
        self.link_hotovo = link_hotovo

    def get_links(self,url:str,link:str,main_link:str) -> dict[str]:
        stranka = httpx.get(url,timeout=10)
        soup = BeautifulSoup(stranka.text, "html.parser")
        result = soup.select(main_link + link)
        return result

    def teams(self) -> list[TeamPageInfo]:
        for link in self.get_links(self.url, self.link_hotovo, 'tbody'):
            self.tymy[link.get_text(strip=True)] = link['href']
                
        vsechny_teamy:list[TeamPageInfo] = []
        for team_name, team_url in self.tymy.items():
            url_tymu = self.hlavni_url + team_url
            jednotlive_teamy = TeamPageInfo(name=team_name, url=url_tymu)
            
            
            staty:list = []
            stats = self.get_links(url_tymu, '.text-center','tbody td')
            for link in stats:

                staty.append(link.get_text(strip=True))
            

            link_id = " .link-secondary[href]"

            jmena = list(self.get_links(url_tymu, link_id,'tbody'))
            

            for i in range(0,len(staty), 6):
                jmeno = jmena[i//6].get_text(strip=True)
                id = str(staty[i])
                utkani = int(staty[i+1])
                goly = int(staty[i+2])
                assistance = int(staty[i+3])
                zlute_karty = int(staty[i+4])
                cervene_karty = int(staty[i+5])
                url = jmena[i//6].get('href')
                
                
                jednotlive_teamy.add_players(PlayerPageInfo(id=id, name=jmeno, url=url, goals=goly, assists=assistance, yellow_cards=zlute_karty, red_cards=cervene_karty, matches_played=utkani, team=team_name, league=""))
            vsechny_teamy.append(jednotlive_teamy)
        return vsechny_teamy

def main():
    hlavni_url = 'https://futsalvplzni.cz'
    url = 'https://futsalvplzni.cz/tymy-statistiky'
    link_hotovo = " .link-secondary[href]"
    crawler = FVPCrawler(hlavni_url, url, link_hotovo)
    teams = crawler.teams()
    print(f"Number of teams: {len(teams)}, Number of players in first team: {teams[0].number_of_players}, First player name: {list(teams[0].players)[0].name}, First player goals: {list(teams[0].players)[0].goals}")

main()