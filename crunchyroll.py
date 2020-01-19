import argparse, glob, threading, json, os, pymediainfo, configparser
import requests, re, time, subprocess, ftfy, shutil, sys, pickle, feedparser
from colorama import Fore, Back, Style, init, Cursor
from datetime import datetime
init(convert=True)

parser = argparse.ArgumentParser(description='Crunchyroll downloading tool')
parser.add_argument("-a", "--aria2c", help="Nutze aria2c statt ffmpeg für nen 'Speedboost'", action='store_true')
parser.add_argument("-b", "--batch", help="Lade alle Links in der CRBatch.txt runter", action='store_true')
parser.add_argument("-r", "--rss", help="Aktiviere den Feedparser", action='store_true')
parser.add_argument("-i", "--info", help="Gib nur Informationen über die Folge aus", action='store_true')
parser.add_argument("-u", "--url", help="Crunchyroll URL")
parser.add_argument("-o","--output", help="Wie die Datei ausgegeben werden soll. Siehe dazu die crunchpy.bat die es nicht gibt")
parser.add_argument("-f", "--folder", help="Ausgabeordner")
parser.add_argument("-q", "--quality", help="480p/720p/1080p")
parser.add_argument("-N", "--noprompt", help="Keine Bestätigung", action='store_true')
parser.add_argument("-U", "--us", help="US Katalog", action='store_true')
parser.add_argument("-S", "--subtitlefixer", help="SubTitleFixer benutzen um die Fonts zu fixen", action='store_true')
parser.add_argument("--forceger", help="Wenn es kein GerSub gibt, dann lade die Subliste neu", action='store_true')
parser.add_argument("-n", "--nomux", help="Nicht muxen", action='store_true')
parser.add_argument("-m", "--move", help="Dateien an einen anderen Ort verschieben", action='store_true')
parser.add_argument("--novideo", help="Nicht muxen", action='store_true')
parser.add_argument("--nologin", help="Überspringt das einloggen allgemein", action='store_true')
parser.add_argument("-k", "--keep", help="Dateien nach dem muxen nicht löschen", action='store_true')
parser.add_argument("--upload", help="Privat", action='store_true')
parser.add_argument("-rs", "--respace", help="Leerzeichen im Dateinamen ersetzen")
parser.add_argument("-rn", "--rename", help="Ersetzt die Namen der Anime durch die in der rename.txt angegeben Namen", action='store_true')
parser.add_argument("-p", "--proxy", help="Proxy. So eingeben: http://Anmeldename:Passwort@ServerAdresse:Port")
parser.add_argument("-e", "--episode", help="Bei welcher Episode er anfangen soll. Ist nur für --season wichtig")
parser.add_argument("-s", "--season", help="Gebe die Seasons an die du runterladen willst. Trenne diese mit einem Leerzeichen. z.B. -s  \"1 2 4\"")
parser.add_argument("--slang", help="Subtitle Languages",default="deDE enUS enUS_ALT esLA esES prBR ruRU itIT arME")
args = parser.parse_args()

cwd = os.getcwd()
os.environ["PATH"] += cwd +'\\bin'+';'
config_file = "cfg\\cr.ini"
cr_config = "cfg\\cr.login"
cr_cookies = "cfg\\cr.cookie"
cr_batch_file = "CRBatch.txt"
version = "3.0.3"

def write_config():
	f = """[episodes]
##Die Collection ID/AoD ID = Die Anzahl der Folgen die er hinzufügen oder entfernen soll. Beipsiele:
##Zieht 12 Episoden ab
22995 = -12
##Fügt 20 Episoden hinzu
25234 = 20
##Fügt 891 hinzu
351 = 891

[rename]
##Die Collection ID/AoD ID = Der neue Name der Serie. Beispiel: 
22995 = Bungo Stray Dogs S02 E
351 = One Piece

[move]
##Verschiebe die Videodateien mit der Collection ID x nach dem Pfad y
#x = y
##Video mit Collection ID 22222 nach C:\\Ich\\Mag\\eX\\nicht
22222 = C:\\Ich\\Mag\\eX\\nicht

[subtitlefixer]
font = Andika New Basic
outline = 1.7
shadow = 0.0

[metadata]
##Metadata, die in die .mkv geschrieben werden soll. Beispiel:
#Ex ist ein... = Faggot
##Sieht so aus https://i.imgur.com/bcoG8rV.png

[feedparser]
##Hier sachen für den Feedparser eintragen. Dafür in diesem Format schreiben: 'Der Anime Name = Der Name im CR Link'
#Beispiel:
Black Clover = black-clover
"""
	g = open(config_file,"w",encoding="utf8")
	g.write(f)
	g.close()

def checkCRStatus():
	statCheck = s.get("https://crunchyroll.com/")
	if not statCheck.status_code == 200:
		print("Eventuell ist deine IP von CR gesperrt oder CR hat derzeit Serverprobleme.")
		print("Errorcode " + str(statCheck.status_code))
		print("Der Source Code wurde dir in cr_error.html geschrieben.")
		with open("cr_error.txt","w",encoding="utf8") as f:
			f.write("f")
		sys.exit(1)

def writeError(link):
	"""https://stackoverflow.com/questions/4706499/how-do-you-append-to-a-file-in-python"""
	with open("CRBatchError.txt", "a") as myfile:
		myfile.write(link + "\n")
	print("Ein Fehler ist aufgetreten.")

def getUSSessionID():
	'''
	Creates a US Session ID where you can access everything from US catalogue without having a US proxy.
	'''
	import random
	for i in range(10):
		try:
			devIDList = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
			devID = ""
			for i in range(32):
				devID += random.choice(devIDList)
			f = s.get("http://api-manga.crunchyroll.com/cr_start_session?api_ver=1.0&device_type=com.crunchyroll.windows.desktop&access_token=LNDJgOit5yaRIWN&device_id="+devID, headers={"Accept-Language":"en"}).json()["data"]["session_id"]
			return f
		except:
			continue
			
def login():
	global session_id
	
	print("[LOGIN] Versuche einzuloggen...")
	if args.nologin:
		if args.us:
			print("[LOGIN] Nicht eingeloggt mit US-Katalog.")
			session_id = getUSSessionID()
			s.cookies.set("session_id", session_id, domain=".crunchyroll.com", path="/")
			s.cookies.set("sess_id", session_id, domain=".crunchyroll.com", path="/")
			s.cookies.set("c_locale", "enUS", domain=".crunchyroll.com", path="/")
		else:
			print("[LOGIN] Nicht eingeloggt.")
			s.get("https://crunchyroll.com/")
			session_id = s.cookies.get_dict()["session_id"]
	else:
		logged_in = False
		if os.path.exists(cr_cookies):
			with open(cr_cookies, 'rb') as f:
				s.cookies.update(pickle.load(f))
				if s.get("https://www.crunchyroll.com/acct",allow_redirects=False).status_code == 200:
					logged_in = True
					print("[LOGIN] Mit Cookies eingeloggt.")
				else:
					logged_in = False
					print("[LOGIN] Cookies veraltet. Logge erneut ein...")
				session_id = s.cookies.get_dict()["session_id"]
		if not logged_in:
			if not os.path.exists(cr_config):
				#Username + Passwort bekommen
				print('[LOGIN] Einmalige Prozedur. Bitte melde dich an. Deine Daten werden in "' + cr_config + '" gespeichert.')
				USER = input("Bitte gib deine E-Mail oder deinen Nutzernamen für CR ein: ")
				PASS = input("Bitte gib dein Passwort für CR ein: ")
				UPDict = {"user":USER, "password": PASS}
				writeUP = open(cr_config,"w",encoding="utf8")
				writeUP.write(json.dumps(UPDict,indent=2))
				writeUP.close()
			else:
				UPDict = json.load(open(cr_config,"r",encoding="utf8"))
				USER = UPDict["user"]
				PASS = UPDict["password"]
			#Session ID bekommen
			session_id = s.cookies.get_dict()["session_id"]
			
			#Einloggen
			loginCheck = s.post("https://api.crunchyroll.com/login.0.json?&locale=enUS&session_id={}&account={}&password={}".format(*[session_id, USER, PASS]))
			try:
				loginCheck = loginCheck.json()
			except:
				print(loginCheck.text)
				print("\n[LOGIN] Dieser Error wurde von CR an dich geschickt. Bitte reporte das")
				sys.exit(1)
			if loginCheck["error"] and loginCheck["code"] == "internal_server_error":
				print("[LOGIN] Interner Server Error bei CR. Versuche es später erneut...")
				print(loginCheck)
				sys.exit(1)
			if loginCheck["error"]:
				print("[LOGIN] Error: " + loginCheck["code"])
				sys.exit(1)
			
			print("[LOGIN] Erfolgreich eingeloggt.")
			#Update die Session_ID nach dem einloggen (Man bekommt eine neue zugewiesen)
			session_id = s.cookies.get_dict()["session_id"]
			if args.us:
				print("[LOGIN] US-Katalog aktiviert.")
				session_id = getUSSessionID()
				s.cookies.set('session_id', session_id, domain=".crunchyroll.com", path="/")
				s.cookies.set('sess_id', session_id, domain=".crunchyroll.com", path="/")
				s.cookies.set('c_locale', "enUS", domain=".crunchyroll.com", path="/")
			
			#Speichere cookies
			with open(cr_cookies, 'wb') as f:
				pickle.dump(s.cookies, f)
			print("[LOGIN] Cookies wurden abgespeichert.")
	print()
#URL Überprüfen und fixen
if args.url is None:
	args.url = input("Bitte gib eine Crunchyroll-URL ein: ")

langlist = ["de","ru","ar","fr","pt-pt","pt-br","es-es","es","en-gb"]
for lang in langlist:
	args.url = args.url.replace("https://www.crunchyroll.com/" + lang + "/","https://www.crunchyroll.com/")
	
#Ausgabeordner
if args.folder is not None:
	if not args.folder.lower() in ["bin","cfg","setup"]:
		if not os.path.exists(args.folder):
			os.mkdir(args.folder)
		folder = args.folder + "\\"
	else:
		folder = ""
else:
	folder = ""
#Erstelle Ordner tmp
if not os.path.exists("tmp"):
	os.mkdir("tmp")

#Wenn kein Output gegeben wurde, nimm den Standard output
if args.output is None:
	args.output = "seriesNameOP epNrOP [Web,qualityOP,AAC]"
if args.respace is not None:
	args.output = args.output.replace(" ", str(args.respace))

#Qualitätseinstellungen
if args.quality is not None:
	QUALITIES = args.quality.strip().split(" ")
else:
	QUALITIES = ["1080p"]

#Konfigurationsdateien
if os.path.exists(config_file):
	
	config = configparser.ConfigParser()
	config.read(config_file, encoding='utf-8-sig')
	episodes_dict = dict(config.items("episodes"))
	rename_dict = dict(config.items("rename"))
	metadataMKV = dict(config.items("metadata"))
	stf = dict(config.items("subtitlefixer"))
	move_dict = dict(config.items("move"))
else:
	write_config()
	print('[SCRIPT] Konfigurationsdatei wurde in "' + config_file + '" geschrieben. Bitte starte das Script neu...')
	sys.exit(0)
if not os.path.exists(cr_batch_file):
	open(cr_batch_file, 'a').close()
	

#Erstelle Session und füge Proxies hinzu, wenn es welche gibt. Checke davor, ob CR online ist
s = requests.session()
if args.proxy is not None:
	s.proxies.update({"http":args.proxy,"https":args.proxy})
checkCRStatus()
login()

def downloadFromCR(url):
	#####GET INFORMATION#####
	def epkiller(episode, collID):
		if args.rename:
			episode = episode + int(episodes_dict.get(collID,0))
		return episode
	def rename(name, collID):
		badCasesList = [":","*","?",".","$",'"',"/","\\",">","<","'","|","(",")"]
		badCasesDict = {"–":"-"}
		for i in badCasesList:
			name = name.replace(i, "")
		for i in badCasesDict:
			name = name.replace(i, badCasesDict[i])
		rawSeriesName = name
		if args.rename:
			name = rename_dict.get(collID, name)
		if args.respace is not None:
			name = name.replace(" ", str(args.respace))
		return rawSeriesName, name
	def getHLSfromURL(url):
		animeWebsite = s.get(url+"?skip_wall=1").text
		streamingMetaData = json.loads(re.findall("vilos\.config\.media = (\{.*?\});",animeWebsite)[0])
		for i in streamingMetaData["streams"]:
			if i["format"] == "adaptive_hls" and i["hardsub_lang"] == None:
				HLS = s.get(i["url"]).json()
	print("Animedaten werden geladen...")
	print()
	while True:
		animeWebsite = s.get(url+"?skip_wall=1",headers={"Accept-Language":"en"}).text
		if "Das ist eine Vorschau" in animeWebsite or "This is a sample clip" in animeWebsite or "Premium-Mitgliedschaft<\\/a> sein, um dies in Ihrer Region anschauen" in animeWebsite or "Premium Membership<\\/a> to watch in your region." in animeWebsite:
			print(Fore.RED+Style.BRIGHT+"Das ist ein Premium-Video und kann nicht gedownloadet werden aufgrund mangelnder Accountrechte(Kein Premium/Nicht eingeloggt).\nBeende..."+Style.RESET_ALL)
			return("skip")
		videoID = url.rsplit("-",1)[1]
		animeMetaData = s.get("http://api.crunchyroll.com/info.0.json?&session_id=" + session_id +"&media_id=" + videoID + "&fields=media.collection_id,media.series_name,media.episode_number",headers={"Accept-Language":"en"}).json()
		collectionID = str(animeMetaData["data"]["collection_id"])
		seriesName = animeMetaData["data"]["series_name"]
		episode_number = animeMetaData["data"]["episode_number"]
		
		streamingMetaData = json.loads(re.findall("vilos\.config\.media = (\{.*?\});",animeWebsite)[0])
		for i in streamingMetaData["streams"]:
			if i["format"] == "adaptive_hls" and i["hardsub_lang"] == None:
				HLS_url = i["url"]
				HLS_tempLang = i["audio_lang"]
				break
		MKVLangDict = {"jaJP":"jpn", "deDE":"ger", "enUS":"eng"}
		mkv_lang = MKVLangDict.get(HLS_tempLang,"und")
		duration = int(str(streamingMetaData["metadata"]["duration"])[:-3])
		
		epMode="0"
		if episode_number != "":
			try:
				episode_number = int(episode_number)
				episode_number = epkiller(episode_number, collectionID)
				episode_number = str(episode_number).zfill(2)
			except:
				try:
					episode_number = float(episode_number)
					episode_number = epkiller(episode_number, collectionID)
					if episode_number<10:
						episode_number = '0'+str(episode_number)
					else:
						episode_number = str(episode_number)
				except:
					pass
				finally:
					epMode="1"
		else:
			episode_number = ""
		rawSeriesName, seriesName = rename(seriesName, collectionID)
		
		
		testedSubs = {"deDE":"Deutsch","esES":"Europäisches Spanish","esLA":"Lateinamerikanisches Spanisch","ptBR":"Brasilianisches Portugiesisch","ruRU":"Russisch","itIT":"Italienisch","arME":"Arabisch"}
		available = []
		for i in streamingMetaData["subtitles"]:
			if i["language"] == "enUS":
				testForAlt = s.get(i["url"]).text
				if "English (US) Alt Track" in testForAlt:
					available.append({"shortLang": "enUS_ALT", "fullLang": "Englisch (Alternative)", "url": i["url"], "filename": folder + rawSeriesName+" "+ episode_number +" [enUS_ALT].ass"})
				else:
					available.append({"shortLang": "enUS", "fullLang": "Englisch", "url": i["url"], "filename": folder + rawSeriesName+" "+ episode_number +" [enUS].ass"})
				continue
			for k in testedSubs:
				if i["language"] == k:
					available.append({"shortLang": k, "fullLang": testedSubs[k], "url": i["url"], "filename": folder + rawSeriesName+" "+episode_number+" ["+k+"].ass"})
		mkv_names = {"deDE":"ger","enUS":"eng","enUS_ALT":"enm","itIT":"ita","esES":"spa","esLA":"spa","prBR":"por","ruRU":"rus","arME":"ara"}
		sublist=[]
		for k in mkv_names:
			for i in available:
				if i["shortLang"] == k and k in args.slang:
					i["mkvLang"] = mkv_names[k]
					sublist.append(i)
		if args.forceger:
			gerInSubs = False
			for i in sublist:
				if i["shortLang"] == "deDE":
					gerInSubs = True
			if not gerInSubs:
				print("Keine deutschen Subs gefunden. Versuche in 30 Sekunden erneut...")
				time.sleep(30)
				continue
		break
		
	m3u8list = s.get(HLS_url).text.strip().split("\n")[1:]
	while True:
		try:
			m3u8list.remove("")
		except:
			break
	is_FHD = False
	is_FHD_done = False
	is_HD = False
	is_HD_done = False
	is_SD = False
	is_SD_done = False
	for i in range(0,len(m3u8list),2):
		info = re.findall("BANDWIDTH=(\d+),RESOLUTION=\d+x(\d+),",m3u8list[i])
		res = int(info[0][1])
		if 720<res and not is_FHD_done:
			if "1080p" in QUALITIES:
				is_FHD = True
			size_FHD = info[0][0]
			url_FHD = m3u8list[i+1]
			is_FHD_done = True
		if 480<res<721 and not is_HD_done:
			if "720p" in QUALITIES:
				is_HD = True
			size_HD = info[0][0]
			url_HD = m3u8list[i+1]
			is_HD_done = True
		if 360<res<481 and not is_SD_done:
			if "480p" in QUALITIES:
				is_SD = True
			size_SD = info[0][0]
			url_SD = m3u8list[i+1]
			is_SD_done = True
			
	sizeVar = []
	if is_SD:
		sizeVar.append("480p: ~"+str(int(int(size_SD)/8*duration/1048576))+"MB")
	if is_HD:
		sizeVar.append("720p: ~"+str(int(int(size_HD)/8*duration/1048576))+"MB")
	if is_FHD:
		sizeVar.append("1080p: ~"+str(int(int(size_FHD)/8*duration/1048576))+"MB")
	sizeVar = " / ".join(sizeVar)
	
	print("Serienname: "+seriesName)
	print("Episodennr.: "+episode_number)
	print("Downloadordner: "+folder[:-1])
	print("Dateigröße: " + sizeVar)
	print("Collection ID: " + collectionID)
	if args.info:
		print("Alle verfügbaren Untertitel: ")
		for i in available:
			print("  [{}] {}".format(i["shortLang"], i["fullLang"]))
		return("skip")
	else:
		for i in sublist:
			print("SUBTITLE: [{}] {}".format(i["shortLang"], i["fullLang"]))
	print()
	if not args.noprompt:
		cont = input("Fortfahren? (y/n): ")
		if not cont.lower() in ["","y","yes","ja"]:
			return("skip")
	
	#####DOWNLOAD#####
	videoname480p = folder + rawSeriesName+" "+episode_number+" [480p].mkv"
	videoname720p = folder + rawSeriesName+" "+episode_number+" [720p].mkv"
	videoname1080p = folder + rawSeriesName+" "+episode_number+" [1080p].mkv"
	output480p = folder + args.output.replace("seriesNameOP",seriesName).replace("epNrOP",episode_number).replace("qualityOP","480p").replace("..",".").replace(",.",",").replace("  "," ") + ".mkv"
	output720p = folder + args.output.replace("seriesNameOP",seriesName).replace("epNrOP",episode_number).replace("qualityOP","720p").replace("..",".").replace(",.",",").replace("  "," ") + ".mkv"
	output1080p = folder + args.output.replace("seriesNameOP",seriesName).replace("epNrOP",episode_number).replace("qualityOP","1080p").replace("..",".").replace(",.",",").replace("  "," ") + ".mkv"
	
	if args.respace is not None:
		seempty=args.respace
	else:
		seempty=" "
	for i in range(1,10):
		output480p = output480p.replace("S0"+str(i)+seempty+"E","S0"+str(i)+"E")
		output720p = output720p.replace("S0"+str(i)+seempty+"E","S0"+str(i)+"E")
		output1080p = output1080p.replace("S0"+str(i)+seempty+"E","S0"+str(i)+"E")
		
	if args.respace is not None:
		seempty=args.respace
	else:
		seempty=" "
	for i in range(1,10):
		output480p = output480p.replace("S0"+str(i)+"E"+seempty,"S0"+str(i)+"E")
		output720p = output720p.replace("S0"+str(i)+"E"+seempty,"S0"+str(i)+"E")
		output1080p = output1080p.replace("S0"+str(i)+"E"+seempty,"S0"+str(i)+"E")
	
	if is_SD and os.path.exists(output480p):
		print("Die 480p existiert schon. Überspringe...")
		is_SD = False
	if is_HD and os.path.exists(output720p):
		print("Die 720p existiert schon. Überspringe...")
		is_HD = False
	if is_FHD and os.path.exists(output1080p):
		print("Die 1080p existiert schon. Überspringe...")
		is_FHD = False
	if False == is_SD == is_HD == is_FHD:
		print("Alle ausgewählen Qualitätsstufen existieren bereits. Überspringe...")
		return("skip")
	print()
	def setProgress(quality, files, max_files, updateString=False, muxing=False):
		global downSD
		global downHD
		global downFHD
		if updateString:
			if quality == "480p":
				downSD = files
			elif quality == "720p":
				downHD = files
			else:
				downFHD = files
		elif quality == "sub":
			#files = filename
			#max_files = 0 bedeutet keine fehler
			#max_files = 1 bedeutet fehler
			global downSubs
			if max_files == 0:
				color = Fore.GREEN
			else:
				color = Fore.RED
			downSubs.append(color + Style.BRIGHT + files + Style.RESET_ALL)
		else:
			currFilesPercent = round(100/max_files*files,2)
			strCurrFilesPercent = format(currFilesPercent, '.2f')
			if currFilesPercent<33:
				colorPerc = Fore.RED
			elif currFilesPercent<67:
				colorPerc = Fore.YELLOW
			else:
				colorPerc = Fore.GREEN
			qualityString = quality + ": " + str(files) + "/" + str(max_files) + " - " + colorPerc + Style.BRIGHT + strCurrFilesPercent + "%" + Style.RESET_ALL 
			if muxing:
				qualityString += " - Konvertiere zu MKV..."
			qualityString += "                "
			
			if quality == "480p":
				downSD = qualityString
			elif quality == "720p":
				downHD = qualityString
			else:
				downFHD = qualityString

	def postProgress():
		if args.aria2c:
			global downSD
			global downHD
			global downFHD
			global downSubs
			time.sleep(1)
			print("\n\n\n")
			while threadSD.isAlive() or threadHD.isAlive() or threadFHD.isAlive():
				print(Cursor.UP(5))
				print(downSD + "\n" + downHD + "\n" + downFHD + "\n" + "Untertitel: " + ", ".join(downSubs))
				time.sleep(1)
		
	def setSyncTrue(sync):
		global syncVideos
		if sync:
			syncVideos = True
	def setSyncFalse():
		global syncVideos
		syncVideos = False
	
	def downloadVideo(quality, videoname, serienname, m3u8URL, episodennummer, enabled):
		if enabled:
			videoname_tmp = videoname[:-4] + "_tmp.mkv"
			setSyncFalse()
			sync = False
			metadataString = ""
			for i in metadataMKV:
				metadataString = metadataString + ' -metadata "' + i + '=' + metadataMKV[i] + '" '
			if os.path.exists(videoname):
				setProgress(quality, quality + ": Die Videodatei existiert bereits.", None, True)
			elif args.aria2c:
				if os.path.exists(videoname_tmp):
					os.remove(videoname_tmp)
						
				#Downloadpfad
				#if args.path:
				#	if not os.path.exists("C:\\crunchpyload"):
				#		os.mkdir("C:\\crunchpyload")
				#	dlfolder = "C:\\crunchpyload\\480_"+serienname.replace(" ","_")+"_"+episodennummer
				#else:
				#	dlfolder = "tmp\\480_"+serienname.replace(" ","_")+"_"+episodennummer
				dlfolder = "tmp\\"+quality+"_"+serienname.replace(" ","_")+"_"+episodennummer
				#Lösche Downloadordner, wenn existiert, da nur tempmüll
				if os.path.exists(dlfolder):
					shutil.rmtree(dlfolder)
				try:
					os.mkdir(dlfolder)
				except:
					pass
				m3u8Content = s.get(m3u8URL).text
				files = re.findall("\n(http.*?\/(seg.*?ts).*?)\n",m3u8Content)
				countFiles = len(files)
				key = re.findall("#EXT-X-KEY:METHOD=AES-128,URI=\"(.*?)\"",m3u8Content)[0]
				
				#Beinhaltet alle download URLs
				writeAriaFull = open(dlfolder+"\\M3U8URLS.full","w",encoding="utf8")
				writeAriaFull.write(m3u8Content+"\n"+key)
				writeAriaFull.close()
				
				#Die m3u8, aber mit richtigem Pfad statt Links
				writeAriaMux = open(dlfolder+"\\M3U8URLS.mux","w",encoding="utf8")
				AriaMux = m3u8Content
				# Ersetzt alle URLs mit Pfaden
				for i in re.findall("https.*?\.mp4\/",AriaMux):
					AriaMux = AriaMux.replace(i,dlfolder+"\\")
				# Ersetzt alle \ zu \\ wegen ffmpeg
				AriaMux = AriaMux.replace("\\","\\\\")
				# Ersetzt alle Parameter
				for i in re.findall("\.ts(.*?)\n",AriaMux):
					AriaMux = AriaMux.replace(i,"")
				for i in re.findall("\.key(.*?)\n",AriaMux):
					AriaMux = AriaMux.replace(i,"\"")
				writeAriaMux.write(AriaMux)
				writeAriaMux.close()
				def downloadAria():
					ariacom = "bin\\aria2c.exe -c -q --enable-color=false --max-file-not-found=10 -q --max-tries=10 --allow-overwrite=true --auto-file-renaming=false --summary-interval=0 --console-log-level=warn -x5 -i \""+dlfolder+"\\M3U8URLS.full\" -d \""+dlfolder+"\""
					subprocess.call(ariacom)
					if len(glob.glob(dlfolder+"\\*.aria2"))>0:
						subprocess.call(ariacom)
				def checkVideo():
					while d0.isAlive():
						length = len(glob.glob(dlfolder+"\\*.ts"))
						setProgress(quality, length, countFiles)
					setProgress(quality, countFiles, countFiles, muxing=True)
				d0 = threading.Thread(target=downloadAria)
				d1 = threading.Thread(target=checkVideo)
				d0.start()
				d1.start()
				d0.join()
				d1.join()
				for i in range(len(files)):
					try:
						if os.path.exists(dlfolder+"\\"+files[i][1]+".aria2"):
							print(Fore.YELLOW+Style.BRIGHT+'Datei "'+files[i][1]+'" fehlt/ist fehlerhaft. Versuche so viel wie möglich zu fixen...'+Style.RESET_ALL)
							tempTS = s.get(files[i][0])
							with open(dlfolder+"\\"+files[i][1],"wb") as writeTS:
								writeTS.write(tempTS.content)
							print(Fore.GREEN+Style.BRIGHT+"Konnte "+str(round(len(tempTS.content)/1048576,2))+"/"+str(round(int(tempTS.headers["Content-Length"])/1048576,2))+" MB laden!"+Style.RESET_ALL)
							sync = True
					except:
						print(Fore.RED+Style.BRIGHT+"Bitte melde diesen Fehler an Tami:"+Style.RESET_ALL)
						raise
				subprocess.call('ffmpeg -allowed_extensions ALL -i "'+dlfolder+'\\M3U8URLS.mux" -c copy -nostdin ' + metadataString + ' -loglevel warning -stats "'+videoname_tmp+'"', stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
				os.rename(videoname_tmp, videoname)
				shutil.rmtree(dlfolder)
			else:
				if os.path.exists(videoname_tmp):
					os.remove(videoname_tmp)
				subprocess.call("ffmpeg.exe -i \""+m3u8URL+"\" -c copy -nostdin " + metadataString + " -loglevel warning -stats \""+videoname_tmp+"\"", stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
				print(Fore.GREEN+Style.BRIGHT+"Die " + quality + " Videodatei wurde heruntergeladen."+Style.RESET_ALL)
				print("")
				os.rename(videoname_tmp,videoname)
			setSyncTrue(sync)
	
	def downloadSubs(subdict):
		for i in subdict:
			if not os.path.exists(i["filename"]):
				download = s.get(i["url"]).text
				download = ftfy.fix_encoding(download)
				writeSub = open(i["filename"],"w",encoding="utf-8")
				writeSub.write(download)
				writeSub.close()
				setProgress("sub", i["fullLang"], 0)
			else:
				setProgress("sub", i["fullLang"], 1)
		
	global downSD
	global downHD
	global downFHD
	global downSubs
	downSD = "480p wird nicht geladen..."
	downHD = "720p wird nicht geladen..."
	downFHD = "1080p wird nicht geladen..."
	downSubs = []
	
	threadProgress = threading.Thread(target=postProgress)
	if is_SD and not args.novideo:
		threadSD = threading.Thread(target=downloadVideo, args=("480p", videoname480p, seriesName, url_SD, episode_number, is_SD))
	else:
		threadSD = threading.Thread()
	if is_HD and not args.novideo:
		threadHD = threading.Thread(target=downloadVideo, args=("720p", videoname720p, seriesName, url_HD, episode_number, is_HD))
	else:
		threadHD = threading.Thread()
	if is_FHD and not args.novideo:
		threadFHD = threading.Thread(target=downloadVideo, args=("1080p", videoname1080p, seriesName, url_FHD, episode_number, is_FHD))
	else:
		threadFHD = threading.Thread()
	threadSubs = threading.Thread(target=downloadSubs, args=[sublist])
	threadProgress.start()
	if is_SD:
		threadSD.start()
	if is_HD:
		threadHD.start()
	if is_FHD:
		threadFHD.start()
	threadSubs.start()
	threadProgress.join()
	if is_SD:
		threadSD.join()
	if is_HD:
		threadHD.join()
	if is_FHD:
		threadFHD.join()
	threadSubs.join()
	print()
	
	if args.subtitlefixer:
		for i in sublist:
			subtitle = open(i["filename"],"r",encoding="utf8").read()
			styles = re.findall('(Style: .*?,)(.*?)(,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,)(.*?)(,)(.*?)(,.*?,.*?,.*?,.*?,.*?)\n',subtitle)
			for j in range(len(styles)):
				if "sign_" in styles[j][0]:
					continue
				subtitle = subtitle.replace(styles[j][0]+styles[j][1]+styles[j][2]+styles[j][3]+styles[j][4]+styles[j][5]+styles[j][6], styles[j][0]+stf["font"]+styles[j][2]+stf["outline"]+styles[j][4]+stf["shadow"]+styles[j][6])
			subtitle = subtitle.replace("\n\n","\n")
			
			subtitleWrite = open(i["filename"],"w",encoding="utf8")
			subtitleWrite.write(subtitle)
			subtitleWrite.close()

	if not args.novideo:
		if is_SD:
			media_info = pymediainfo.MediaInfo.parse(videoname480p).to_data()
		elif is_HD:
			media_info = pymediainfo.MediaInfo.parse(videoname720p).to_data()
		else:
			media_info = pymediainfo.MediaInfo.parse(videoname1080p).to_data()
		for i in range(len(media_info["tracks"])):
			if media_info["tracks"][i]["track_type"] == "Video":
				frame_rate = media_info["tracks"][i]["frame_rate"]

	
	for i in sublist:
		subfilename = i["filename"]
		tmp_subfilename = i["filename"] + "_tmp.ass"
		subprocess.call('python bin\\newprass.py copy-styles --resample --from cfg\\template.ass --to "'+subfilename+'" -o "'+tmp_subfilename+'"')
		g=open(tmp_subfilename, "r", encoding="utf8")
		f=g.read()
		g.close()
		if "ScaledBorderAndShadow: no" in f:
			f = f.replace("ScaledBorderAndShadow: no", "ScaledBorderAndShadow: yes")
		elif not "ScaledBorderAndShadow: yes" in f:
			f=f.replace("[Script Info]", "[Script Info]\nScaledBorderAndShadow: yes")
		
		g=open(tmp_subfilename, "w", encoding="utf8")
		g.write(f)
		g.close()
		
		os.remove(subfilename)
		os.rename(tmp_subfilename, subfilename)
	
	def mux_progress(cmd,videofile,muxfile):
		def muxProgress(vidfile,mxfile):
			filesize = int(os.path.getsize(vidfile)/1048576)
			while t1.isAlive():
				try:
					muxsize = int(os.path.getsize(mxfile)/1048576)
				except FileNotFoundError:
					continue
				muxPercentage = round(100/filesize*muxsize,2)
				if muxPercentage>100:
					muxPercentage = 100
				muxPercentage2 = format(muxPercentage, '.2f')
				print(muxPercentage2 + "% - " + str(muxsize) + " MB/" + str(filesize) + " MB")
				time.sleep(0.2)
				print(Cursor.UP(2))
			print("100.00% - " + str(filesize) + " MB/" + str(filesize) + " MB                   ")
			print(Cursor.UP(2))
		def muxCommand(command):
			os.system(command)
		t1 = threading.Thread(target=muxCommand,args=([cmd]))
		t0 = threading.Thread(target=muxProgress,args=(videofile,muxfile))
		t1.start()
		t0.start()
		t1.join()
		t0.join()
		
	if not args.nomux and not args.novideo:
		global modus
		subVar = ""
		for i in range(len(sublist)):
			if i == 0:
				subVar = subVar +  '--sub-charset 0:UTF-8 --language 0:'+sublist[i]["mkvLang"]+' --default-track 0:yes --forced-track 0:yes --track-name "0:'+sublist[i]["fullLang"]+'" -s 0 -D -A -T ( "'+sublist[i]["filename"]+'" ) '
			else:
				subVar = subVar +  '--sub-charset 0:UTF-8 --language 0:'+sublist[i]["mkvLang"]+' --default-track 0:no --forced-track 0:no --track-name "0:'+sublist[i]["fullLang"]+'" -s 0 -D -A -T ( "'+sublist[i]["filename"]+'" ) '
		
		fontList = glob.glob("cfg\\*.ttf") + glob.glob("cfg\\*.otf")
		fontVar = ""
		for x in fontList:
			fontVar += " --attachment-mime-type application/x-truetype-font --attach-file " + x
			
		if syncVideos == False:
			fps = " --default-duration 0:"+frame_rate+"fps "
		else:
			fps = ""
		
		muxDict = [{"videoname":videoname480p,"outputname":output480p, "enabled": is_SD, "quality": "480p"},
		{"videoname":videoname720p,"outputname":output720p, "enabled": is_HD, "quality": "720p"},
		{"videoname":videoname1080p,"outputname":output1080p, "enabled": is_FHD, "quality": "1080p"}]
		for i in muxDict:
			if i["enabled"]:
				print("Muxe {}...".format(i["quality"]))
				command = 'mkvmerge.exe --quiet -o "' + i["outputname"] + '" --language 0:jpn --default-track 0:yes --forced-track 0:yes ' + fps + ' --fix-bitstream-timing-information 0:1 --language 1:' + mkv_lang + ' --default-track 1:yes --forced-track 1:yes -a 1 -d 0 -S -T ( "' + i["videoname"] + '" ) ' +  subVar + fontVar
				mux_progress(command,i["videoname"],i["outputname"])
				print()
	
	videos = {output480p:is_SD, output720p:is_HD, output1080p:is_FHD}
	if args.move:
		for i in move_dict:
			if i == collectionID:
				for j in videos:
					if videos[j]:
						shutil.move(j,move_dict[i])
						print('"'+j+ '" wurde nach "' + move_dict[i] + '" verschoben.')
				break

	names = [videoname480p,videoname720p,videoname1080p]
	if args.keep or args.nomux or args.novideo:
		pass
	else:
		for x in names:
			if os.path.exists(x):
				os.remove(x)
		for x in sublist:
			if os.path.exists(x["filename"]):
				os.remove(x["filename"])

	if args.upload:
		if os.path.exists("RVOL2.py"):
			call('py -3.6 RVOL2.py -t "abc" -m "'+epMode+'" -f72 "'+output720p+'" -f18 "'+output1080p+'" -e -f -ep '+episode_number)
if args.rss:
	def download(link,subExist):
		feed_config = configparser.ConfigParser()
		feed_config.read(config_file, encoding='utf-8-sig')
		feed_dict = dict(feed_config.items("feedparser"))
		
		for j in feed_dict:
			if feed_dict[j] in link and subExist==True:
				downloadFromCR(link)
				return
			elif feed_dict[j] in link and subExist==False:
				checker.append(link)
				return
	def parse_feed():
		while True:
			try:
				while True:
					try:
						feed = feedparser.parse(s.get("https://www.crunchyroll.com/rss/anime?lang=deDE").text)
						break
					except:
						print("Fehler beim Bekommen des Feeds. Versuche erneut...")
						continue
				if len(feed.entries) == 0:
					continue
				AnimeID = open(latest_entry, 'r', encoding="utf8").read()
				if AnimeID == "":
					g = open(latest_entry, "w", encoding="utf8")
					g.write(feed.entries[0]["id"])
					g.close()
					print('Entry in ' + str(latest_entry) +' was invalid and has been replaced with the newest Entry.')
					break
				UpdateAID = open(latest_entry, "w", encoding="utf8")#Schreibt den neusten Eintrag aus dem Feed in die Datei.
				UpdateAID.write(feed.entries[0]["id"])#Wichtig: der Alte eintrag ist in h gespeichert
				UpdateAID.close()
				for entryid in range(len(feed.entries)):
					for i in checker:
						try:
							if feed.entries[entryid].link == i and "de - de" in feed.entries[entryid]["crunchyroll_subtitlelanguages"]:
								time.sleep(60)
								download(i,True)
								checker.remove(i)
						except KeyError:
							pass
				for entryid in range(len(feed.entries)):
					subExist = False
					try:
						if "de - de" in feed.entries[entryid]["crunchyroll_subtitlelanguages"]:
							subExist = True
						else:
							subExist = False
					except:
						pass
					feedAnimeID = feed.entries[entryid]["id"]
					active = False
					if AnimeID == feedAnimeID:
						break
					else:
						History = json.load(open(used_entries,"r",encoding="utf8"))
						if feedAnimeID in History:
							active = True
						if active == False:
							History.append(feedAnimeID)
							AddNewFeed = open(used_entries,"w",encoding="utf8")
							AddNewFeed.write(json.dumps(History))
							AddNewFeed.close()
							print("Added " + feedAnimeID)
							download(feed.entries[entryid].link, subExist)
					
					
					
						
				break
			except IndexError:
				time.sleep(5)
				continue
				
	args.forceger = True
	args.noprompt = True
	checker = []
	latest_entry = "cfg\\CRLatestEntry.txt"
	used_entries = "cfg\\CRUsedEntries.txt"
	
	if not os.path.exists(used_entries):
		g = open(used_entries,"w",encoding="utf8")
		g.write("[]")
		g.close()
	
	feed = feedparser.parse(s.get("https://www.crunchyroll.com/rss/anime?lang=deDE").text)
	g = open(latest_entry,"w")
	g.write(feed.entries[0]["id"])
	g.close()
	print("Die neuste Crunchyroll ID wurde im Feed geupdatet\n")
	
	while True:
		parse_feed()
		print(str(datetime.now().strftime('%d %H-%M-%S'))+" - - - "+str(checker))
		for count in range(30, 0, -1):
			print("Warte "+str(count)+" Sekunden ")
			time.sleep(1)
			print(Cursor.UP(2))
		print("\n")
elif args.batch:
	f = open(cr_batch_file,"r",encoding="utf8").read()
	f = f.split("\n")
	for i in f:
		if i.startswith("http://www.crunchyroll.com/"):
			i = i.replace("http://", "https://")
		if not i.startswith("https://www.crunchyroll.com/"):
			continue
		try:
			downloadFromCR(i)
		except:
			writeError(i)
			pass
elif args.season is not None or args.url.count("/")<4:
	args.noprompt = True
	if args.url.count("/")>3:
		args.url = args.url.rsplit("/",1)[0]
	if args.episode is not None:
		episodesToSkip = int(args.episode)-1
	else:
		episodesToSkip = 0
	CRhtml = s.get(args.url + "?skip_wall=1").text
	multiSeasons = re.findall("title=\".*?\">(.*?)<\/a>\n\s*<ul class=\"portrait-grid cf\" style=\".*?\">\n\s*<li id=\".*?\" class=\"hover-bubble group-item\">\n\s*<div class=\"wrapper container-shadow hover-classes\" data-classes=\"container-shadow-dark\">\n\s*<a href=\"(.*?)\" title=\".*?\"",CRhtml)
	multiSeasons.reverse()
	if len(multiSeasons) == 0:
		print("Eine Staffel erkannt.")
	else:
		for i in range(len(multiSeasons)):
			print("Staffel "+str(i+1)+": "+multiSeasons[i][0])
		if args.season is None:
			print("(Trenne Staffeln durch Leerzeichen)")
			args.season = input("Bitte gib die Staffeln ein, die du runter laden willst: ")
			print()
			args.season = args.season.strip().split(" ")
		print("Es werden folgende Staffeln runtergeladen: " + ",".join(args.season))
	os.system("pause")
	if len(multiSeasons) == 0:
		multiEpisodes = re.findall("<li id=\".*?\" class=\"hover-bubble group-item\">\n\s*<div class=\"wrapper container-shadow hover-classes\" data-classes=\"container-shadow-dark\">\n\s*<a href=\"(.*?)\" title=\".*?\"",CRhtml)
		for i in range(len(multiEpisodes)):
			multiEpisodes[i] = "https://crunchyroll.com" + multiEpisodes[i]
		multiEpisodes.reverse()
		while episodesToSkip != 0:
			multiEpisodes = multiEpisodes[1:]
			episodesToSkip -= 1
		print("Lade "+str(len(multiEpisodes)) + " Episoden herunter.")
		os.system("pause")
		for i in multiEpisodes:
			try:
				downloadFromCR(i)
			except:
				writeError(i)
				pass
	else:
		links=[]
		episodeList=[]
		seasonList=[]
		seasonNames=[]
		for i in range(len(multiSeasons)):
			if str(i+1) in args.season:
				seasonNames.append(multiSeasons[i][0])
		#if args.us:
		#	session_id = getUSSessionID()
		for i in range(len(multiSeasons)):
			if str(i+1) in args.season:
				epID = multiSeasons[i][1].rsplit("-",1)[1]
				getCollID = s.get("http://api.crunchyroll.com/info.0.json?&session_id="+session_id+"&media_id="+str(epID)).text
				try:
					CollID = json.loads(getCollID)["data"]["collection_id"]
				except:
					print(getCollID)
					print(s.cookies)
					print("http://api.crunchyroll.com/info.0.json?&session_id="+session_id+"&media_id="+str(epID))
					print("\nBitte überprüfe ob das die richtige ID bei CR ist: "+str(epID))
					print("Es besteht aber auch die Möglichkeit, dass die API derzeit wegen CloudFlare down ist. Siehe http://tiny.cc/eXsucKs")
					raise
				
				#getCollID = s.get("https://crunchyroll.com" + multiSeasons[i][1]).text
				#CollID = json.loads(re.findall("mediaMetadata = (\{.*?\});",getCollID)[0])["collection_id"]
				animeInfo = json.loads(s.get("http://api.crunchyroll.com/list_media.0.json?&session_id="+session_id+"&collection_id="+str(CollID)+"&limit=1000").text)
				for j in range(len(animeInfo["data"])):
					if episodesToSkip != 0:
						episodesToSkip -= 1
						continue
					links.append(animeInfo["data"][j]["url"])
				episodeList.append(len(animeInfo["data"]))
				seasonList.append(i+1)
		for i in range(len(seasonList)):
			print("Lade "+Fore.GREEN+Style.BRIGHT+"Staffel "+str(seasonList[i])+Style.RESET_ALL+" / "+Fore.GREEN+Style.BRIGHT+seasonNames[i]+Style.RESET_ALL+" mit "+Fore.GREEN+Style.BRIGHT+str(episodeList[i])+Style.RESET_ALL+" Episoden herunter.")
		for i in links:
			try:
				downloadFromCR(i)
			except:
				writeError(i)
				pass
	exit()
else:
	downloadFromCR(args.url)








