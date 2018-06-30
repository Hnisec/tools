#!/usr/bin/env python3
# -*- coding: latin-1 -*- ######################################################
#                ____                     _ __                                 #
#     ___  __ __/ / /__ ___ ______ ______(_) /___ __                           #
#    / _ \/ // / / (_-</ -_) __/ // / __/ / __/ // /                           #
#   /_//_/\_,_/_/_/___/\__/\__/\_,_/_/ /_/\__/\_, /                            #
#                                            /___/ team                        #
#                                                                              #
# dnsspider.py - async multithreaded subdomain bruteforcer                     #
#                                                                              #
# DESCRIPTION                                                                  #
# A very fast async multithreaded bruteforcer of subdomains that leverages a   #
# wordlist and/or character permutation.                                       #
#                                                                              #
# AUTHOR                                                                       #
# noptrix - http://www.nullsecurity.net/                                       #
#                                                                              #
# NOTES:                                                                       #
# quick'n'dirty code                                                           #
#                                                                              #
# TODO:                                                                        #
# - check if we have to scan if wildcard enabled                               #
#                                                                              #
# CHANGELOG:                                                                   #
#                                                                              #
# v1.0                                                                         #
# - attack while mutating (don't generate whole list when using -t 1) (bugfix) #
# - update built-in wordlist (more than 8k!)                                   #
#                                                                              #
# v0.9                                                                         #
# - use async multithreading via concurrent.futures module                     #
# - attack while mutating -> don't generate whole list when using -t 1         #
# - log only the subdomains to logfile when '-r' was chosen                    #
# - minor code clean-ups / refactoring                                         #
# - switch to tabstop=2 / shiftwidth=2                                         #
#                                                                              #
# v0.8                                                                         #
# - upgraded to python3                                                        #
#                                                                              #
# v0.7                                                                         #
# - upgraded built-in wordlist (more than 2k)                                  #
# - remove annoying timeout warnings                                           #
# - remove color output when logging to file                                   #
#                                                                              #
# v0.6                                                                         #
# - upgraded default wordlist                                                  #
# - replaced optionparser with argparse                                        #
# - add version output option                                                  #
# - fixed typo                                                                 #
#                                                                              #
# v0.5                                                                         #
# - fixed extracted ip addresses from rrset answers                            #
# - renamed file (removed version string)                                      #
# - removed trailing whitespaces                                               #
# - removed color output                                                       #
# - changed banner                                                             #
#                                                                              #
# v0.4                                                                         #
# - fixed a bug for returned list                                              #
# - added postfix option                                                       #
# - upgraded wordlist[]                                                        #
# - colorised output                                                           #
# - changed error messages                                                     #
#                                                                              #
# v0.3:                                                                        #
# - added verbose/quiet mode - default is quiet now                            #
# - fixed try/catch for domainnames                                            #
# - fixed some tab width (i normally use <= 80 chars per line)                 #
#                                                                              #
# v0.2:                                                                        #
# - append DNS and IP output to found list                                     #
# - added diffound list for subdomains resolved to different addresses         #
# - get right ip address from current used iface to avoid socket problems      #
# - fixed socket exception syntax and output                                   #
# - added usage note for fixed port and multithreaded socket exception         #
#                                                                              #
# v0.1:                                                                        #
# - initial release                                                            #
################################################################################


import sys
import time
import string
import itertools
import socket
import re
import argparse
from concurrent.futures import ThreadPoolExecutor
try:
  import dns.message
  import dns.query
except ImportError:
  print("[-] ERROR: you need the 'dnspython' package")
  sys.exit()


BANNER = '--==[ dnsspider by noptrix@nullsecurity.net ]==--'
USAGE = '\n' \
  '  dnsspider.py -t <arg> -a <arg> [options]'
VERSION = 'v1.0'

defaults = {}
hostnames = []
prefix = ''
postfix = ''
found = []
diffound = []
chars = string.ascii_lowercase
digits = string.digits

# default wordlist
wordlist = [
'0', '01', '02', '03', '0_', '1', '10', '100', '101', '102', '103', '104',
'105', '106', '107', '108', '109', '11', '110', '111', '11192521403954',
'11192521404255', '112', '11285521401250', '11290521402560', '113', '114',
'115', '116', '117', '118', '119', '12', '120', '121', '122', '123', '124',
'125', '126', '127', '128', '129', '13', '130', '131', '132', '133', '134',
'135', '136', '137', '138', '139', '14', '140', '141', '142', '143', '144',
'145', '146', '147', '148', '149', '15', '150', '151', '152', '153', '154',
'155', '156', '157', '158', '159', '16', '160', '161', '162', '163', '164',
'165', '166', '167', '168', '169', '17', '170', '172', '173', '174', '175',
'176', '177', '178', '179', '18', '180', '181', '182', '183', '184', '185',
'186', '187', '188', '189', '19', '190', '191', '192', '193', '194', '195',
'196', '197', '198', '199', '1c', '1rer', '2', '20', '200', '2008', '2009',
'201', '2010', '2011', '2012', '2013', '202', '203', '204', '205', '206',
'207', '208', '209', '21', '210', '211', '212', '213', '214', '215', '216',
'217', '218', '219', '22', '220', '221', '222', '223', '224', '225', '226',
'227', '228', '229', '23', '230', '231', '232', '233', '234', '235', '236',
'237', '238', '239', '24', '240', '241', '242', '243', '244', '245', '246',
'247', '248', '249', '25', '250', '251', '252', '253', '254', '255', '26',
'27', '28', '29', '2tty', '3', '30', '31', '32', '33', '34', '35', '36', '37',
'38', '39', '3com', '3d', '3g', '4', '40', '41', '42', '43', '44', '45', '46',
'47', '48', '49', '4k', '5', '50', '51', '52', '53', '54', '55', '56', '57',
'58', '59', '6', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69',
'7', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '8', '80',
'81', '82', '83', '84', '85', '86', '87', '88', '89', '9', '90', '91', '911',
'92', '93', '94', '95', '96', '97', '98', '98-62', '99', 'ILMI', 'a',
'a.auth-ns', 'a.mx', 'a.ns', 'a.ns.e', 'a0', 'a01', 'a02', 'a1', 'a2', 'a3',
'a4', 'a5', 'a6', 'a7', 'aa', 'aaa', 'aaaa', 'aaron', 'ab', 'abbot', 'abc',
'abcd', 'abhsia', 'abo', 'about', 'abs', 'abu', 'abuja', 'abuse',
'abuse-report', 'ac', 'acacia', 'academico', 'academy', 'acc', 'acceso',
'access', 'account', 'accounting', 'accounts', 'accra', 'acct4', 'acct4-cert',
'ace', 'acessonet', 'achilles', 'acid', 'acm', 'acme', 'acs', 'act', 'action',
'activate', 'active', 'activestat', 'activity', 'ad', 'ad1', 'ad2', 'ad3',
'ada', 'adam', 'add', 'addis', 'adfs', 'adimg', 'adkit', 'adm', 'adm2',
'admin', 'admin.test', 'admin1', 'admin2', 'admin3', 'administracion',
'administrador', 'administration', 'administrator', 'administrators', 'admins',
'admission', 'admissions', 'adonis', 'adrian', 'adrian.users', 'ads', 'ads2',
'adsense', 'adserver', 'adserver2', 'adsl', 'adslgp', 'adslnat-curridabat-128',
'adult', 'adv', 'advance', 'advert', 'advertising', 'ae', 'af', 'aff',
'affiliate', 'affiliates', 'affiliati', 'afiliados', 'afisha', 'africa',
'afrodita', 'ag', 'age', 'agency', 'agenda', 'agent', 'agk', 'agora', 'agri',
'agro', 'ah', 'ai', 'aida', 'aim', 'ain', 'air', 'aire', 'ais', 'aix', 'ajax',
'ak', 'akamai', 'al', 'alabama', 'alaska', 'alba', 'albert', 'albq', 'album',
'albuquerque', 'aleph', 'alert', 'alerts', 'alestra', 'alex', 'alex.users',
'alexander', 'alexandra', 'alf', 'alfa', 'alfresco', 'algiers', 'alice', 'all',
'all-nodes', 'all.edge', 'all.videocdn', 'allegro', 'alliance', 'alma', 'alpha',
'alt', 'alt-host', 'altair', 'alterwind', 'alumni', 'am', 'amanda', 'amarillo',
'amazon', 'amedd', 'americas', 'amman', 'ams', 'amsterdam', 'amur', 'an', 'ana',
'anaheim', 'analytics', 'analyzer', 'and', 'andorra', 'andrea', 'andrew',
'android', 'andromeda', 'andy', 'angel', 'angels', 'anhth', 'animal', 'anime',
'ankara', 'anketa', 'ann', 'anna', 'announce', 'announcements', 'annuaire',
'answers', 'ant', 'antananarivo', 'antares', 'anthony', 'antispam', 'antivir',
'antivirus', 'anton', 'anubis', 'anubis-01', 'anubis-02', 'anubis-03',
'anubis-1', 'anubis-2', 'anubis-3', 'anubis01', 'anubis02', 'anubis03',
'anubis1', 'anubis2', 'anubis3', 'anunturi', 'anywhere', 'ao', 'aol', 'ap',
'ap1', 'apache', 'apc', 'apc1', 'apex', 'apg', 'aphrodite', 'api', 'api-1',
'api-2', 'api-3', 'api-4', 'api-5', 'api-6', 'api-7', 'api-8', 'api-mobile',
'api-test', 'api.news', 'api1', 'api1-backup', 'api2', 'api2-backup',
'api3-backup', 'api4-backup', 'api5-backup', 'api6-backup', 'apia', 'apis',
'apol', 'apollo', 'app', 'app01', 'app1', 'app2', 'app3', 'appdev', 'apple',
'application', 'applications', 'applwi', 'apply', 'apps', 'apps2', 'appserver',
'aproxy', 'aps', 'apt', 'aptest', 'aq', 'aqua', 'aquarius', 'aquila', 'ar',
'ara', 'araba', 'arabic', 'aragorn', 'arc', 'arcadia', 'arch', 'archer',
'archie', 'archiv', 'archive', 'archives', 'arcsight', 'area', 'arena', 'ares',
'argentina', 'argo', 'argon', 'argos', 'aria', 'ariel', 'aries', 'arizona',
'arkansas', 'arlington', 'arm', 'arpa', 'ars', 'art', 'artemis', 'arthur',
'article', 'articles', 'artifactory', 'arts', 'arwen', 'as', 'as1', 'as2',
'as400', 'asa', 'asb', 'asdf', 'asf', 'asgard', 'ash', 'ashgabat', 'asia',
'asianet', 'ask', 'asm', 'asmara', 'asp', 'aspire', 'assembla', 'asset',
'assets', 'assets1', 'assets2', 'assets3', 'assets4', 'assets5', 'assets6',
'assist', 'ast', 'astana', 'asterisk', 'asterix', 'astra', 'astro', 'astun',
'asuncion', 'at', 'atc', 'atd', 'athena', 'athens', 'atlanta', 'atlantic',
'atlantis', 'atlas', 'atlassian', 'atlassian-01', 'atlassian-02',
'atlassian-03', 'atlassian-1', 'atlassian-2', 'atlassian-3', 'atlassian01',
'atlassian02', 'atlassian03', 'atlassian1', 'atlassian2', 'atlassian3', 'atm',
'atollon', 'atom', 'atrium', 'ats', 'att', 'attask', 'attix', 'attix5', 'au',
'auction', 'auctions', 'audi', 'audio', 'audit', 'aura', 'aurora', 'austin',
'australia', 'austtx', 'auth', 'auth-hack', 'auth1', 'auth2', 'auth3', 'author',
'auto', 'autoconfig', 'autoconfig.admin', 'autoconfig.ads', 'autoconfig.beta',
'autoconfig.blog', 'autoconfig.cdn', 'autoconfig.chat', 'autoconfig.crm',
'autoconfig.demo', 'autoconfig.dev', 'autoconfig.directory', 'autoconfig.email',
'autoconfig.en', 'autoconfig.es', 'autoconfig.forum', 'autoconfig.forums',
'autoconfig.images', 'autoconfig.img', 'autoconfig.jobs', 'autoconfig.m',
'autoconfig.mail', 'autoconfig.media', 'autoconfig.mobile', 'autoconfig.new',
'autoconfig.news', 'autoconfig.old', 'autoconfig.search', 'autoconfig.secure',
'autoconfig.shop', 'autoconfig.sms', 'autoconfig.staging', 'autoconfig.static',
'autoconfig.store', 'autoconfig.support', 'autoconfig.test',
'autoconfig.travel', 'autoconfig.video', 'autoconfig.videos',
'autoconfig.webmail', 'autoconfig.wiki', 'autodiscover', 'autodiscover.admin',
'autodiscover.ads', 'autodiscover.beta', 'autodiscover.blog',
'autodiscover.cdn', 'autodiscover.chat', 'autodiscover.crm',
'autodiscover.demo', 'autodiscover.dev', 'autodiscover.directory',
'autodiscover.email', 'autodiscover.en', 'autodiscover.es',
'autodiscover.forum', 'autodiscover.forums', 'autodiscover.images',
'autodiscover.img', 'autodiscover.jobs', 'autodiscover.m', 'autodiscover.mail',
'autodiscover.media', 'autodiscover.mobile', 'autodiscover.new',
'autodiscover.news', 'autodiscover.old', 'autodiscover.search',
'autodiscover.secure', 'autodiscover.shop', 'autodiscover.sms',
'autodiscover.staging', 'autodiscover.static', 'autodiscover.store',
'autodiscover.support', 'autodiscover.test', 'autodiscover.travel',
'autodiscover.video', 'autodiscover.videos', 'autodiscover.webmail',
'autodiscover.wiki', 'automatedqa', 'automn', 'automotive', 'autoreply',
'autorun', 'autos', 'av', 'ava', 'available', 'avalon', 'avantel', 'avatar',
'avatars', 'avia', 'avto', 'aw', 'award', 'awards', 'aws', 'awstats', 'axis',
'ayuda', 'az', 'azmoon', 'azure', 'b', 'b.auth-ns', 'b.ns', 'b.ns.e', 'b01',
'b02', 'b1', 'b2', 'b2b', 'b2c', 'b3', 'b5', 'ba', 'baby', 'bach', 'back',
'backend', 'backoffice', 'backtrack', 'backup', 'backup-1', 'backup1',
'backup2', 'backup3', 'backups', 'bacula', 'badboy', 'baghdad', 'baidu',
'baijiale', 'bak', 'baker', 'bakersfield', 'baku', 'balance', 'balancer',
'balder', 'bali', 'baltimore', 'bamako', 'bambi', 'bamboo', 'banana', 'bancuri',
'bandar', 'bandwidth', 'bangkok', 'bangui', 'banjul', 'bank', 'banking',
'banner', 'banners', 'baobab', 'bar', 'barnaul', 'barney', 'barracuda',
'barracuda2', 'bart', 'base', 'baseball', 'basecamp', 'basseterre', 'bastion',
'batman', 'bayarea', 'baza', 'bazaar', 'bb', 'bbb', 'bbdd', 'bbs', 'bbtest',
'bc', 'bcast', 'bchsia', 'bcvloh', 'bd', 'bdc', 'bdc1', 'bdsm', 'be', 'bea',
'beacon', 'beagle', 'bean', 'bear', 'beast', 'beauty', 'bee', 'beer', 'beijing',
'beirut', 'belfast', 'belgrade', 'bell', 'belmopan', 'ben', 'bender', 'berlin',
'bern', 'berry', 'bes', 'best', 'bet', 'beta', 'beta.m', 'beta1', 'beta2',
'beta3', 'betastream', 'betterday.users', 'betty', 'bf', 'bg', 'bgk', 'bh',
'bhm', 'bi', 'bib', 'biblio', 'biblioteca', 'bid', 'big', 'big5', 'bigbrother',
'bigpond', 'bike', 'bilbo', 'bill', 'billing', 'bingo', 'bio', 'biologie',
'biology', 'biotech', 'bip', 'bird', 'birmingham', 'bis', 'bishkek', 'bissau',
'bit', 'bitex', 'bitkeeper', 'biz', 'biznes', 'biztalk', 'bj', 'bk', 'bkp',
'bl', 'black', 'blackberry', 'blackboard', 'blackbox', 'blackhole', 'blackjack',
'blacklist', 'blade', 'blade1', 'blade2', 'blah', 'blast', 'bliss', 'blog',
'blog1', 'blog2', 'blogger', 'blogs', 'blogtest', 'blogx.dev', 'bloom', 'blue',
'bluesky', 'blueyonder', 'bm', 'bms', 'bmw', 'bn', 'bna', 'bnc', 'bo', 'boa',
'board', 'boards', 'bob', 'bocaiwang', 'bof', 'bogota', 'bois', 'boise', 'bol',
'bolsa', 'bonobo', 'bonobo-01', 'bonobo-02', 'bonobo-03', 'bonobo-1',
'bonobo-2', 'bonobo-3', 'bonobo01', 'bonobo02', 'bonobo03', 'bonobo1',
'bonobo2', 'bonobo3', 'bonus', 'book', 'booking', 'bookmark', 'books',
'bookstore', 'boom', 'bootp', 'border', 'boss', 'boston', 'bot', 'boulder',
'bounce', 'bounces', 'bound', 'boutique', 'box', 'box1', 'boy', 'bp', 'bpb',
'bpm', 'br', 'brain', 'branch', 'brand', 'brasilia', 'brasiltelecom',
'bratislava', 'bravo', 'brazil', 'brazzaville', 'bredband', 'bridge',
'bridgetown', 'brightwork', 'britian', 'bro', 'bro-01', 'bro-02', 'bro-03',
'bro-1', 'bro-2', 'bro-3', 'bro01', 'bro02', 'bro03', 'bro1', 'bro2', 'bro3',
'broadband', 'broadcast', 'broadwave', 'broker', 'bromine', 'bronx', 'bronze',
'brown', 'brs', 'bruno', 'brussels', 'brutus', 'bryan', 'bs', 'bsc', 'bsd',
'bsd0', 'bsd01', 'bsd02', 'bsd1', 'bsd2', 'bsdi', 'bss', 'bt', 'btas', 'bts',
'bucharest', 'budapest', 'buddy.webchat', 'budget', 'buenos', 'buffalo', 'bug',
'buggalo', 'bugs', 'bugtracker', 'bugzilla', 'build', 'build-01', 'build-02',
'build-03', 'build-1', 'build-2', 'build-3', 'build01', 'build02', 'build03',
'build1', 'build2', 'build3', 'builder', 'builder.control',
'builder.controlpanel', 'builder.cp', 'builder.cpanel', 'bujumbura', 'bulk',
'bulletins', 'bunny', 'burn', 'burner', 'bus', 'buscador', 'business',
'businessdriver', 'butler', 'buy', 'buzz', 'bv', 'bw', 'bwc', 'by', 'bz', 'c',
'c-n7k-n04-01.rz', 'c-n7k-v03-01.rz', 'c.auth-ns', 'c.ns.e', 'c1', 'c2', 'c3',
'c3po', 'c4', 'c4anvn3', 'c5', 'c6', 'ca', 'cabinet', 'cable', 'cache',
'cache1', 'cache2', 'cache3', 'cacti', 'cactus', 'cad', 'cae', 'cafe', 'cag',
'cairo', 'cake', 'cal', 'calc', 'caldera', 'calendar', 'california', 'call',
'callcenter', 'callisto', 'calvin', 'calypso', 'cam', 'cam1', 'cam2', 'camel',
'camera', 'cameras', 'campaign', 'camping', 'campus', 'cams', 'can', 'canada',
'canal', 'canberra', 'cancer', 'candy', 'canli', 'canon', 'canvas', 'cap',
'capacitacion', 'capricorn', 'car', 'caracas', 'carbon', 'card', 'cardiff',
'cards', 'care', 'career', 'careers', 'cargo', 'carmen', 'carpediem', 'cars',
'cart', 'cas', 'cas1', 'cas2', 'casa', 'case', 'cash', 'casino', 'casper',
'castor', 'castries', 'cat', 'catalog', 'catalogo', 'catalogue', 'catchlimited',
'cats', 'cayenne', 'cb', 'cbf1', 'cbf2', 'cbf3', 'cbf8', 'cc', 'ccc', 'ccgg',
'ccs', 'cctv', 'cd', 'cdburner', 'cdc', 'cdn', 'cdn-1', 'cdn-2', 'cdn-3',
'cdn1', 'cdn101', 'cdn2', 'cdn3', 'cdntest', 'cdp', 'cds', 'ce', 'cell',
'center', 'centos', 'central', 'centraldesktop', 'cerberus', 'cerebro', 'ceres',
'cert', 'certificates', 'certify', 'certserv', 'certsrv', 'ces', 'cf',
'cf-protected', 'cf-protected-www', 'cfd185', 'cfd297', 'cg', 'cgi', 'cgit',
'cgit-01', 'cgit-02', 'cgit-03', 'cgit-1', 'cgit-2', 'cgit-3', 'cgit01',
'cgit02', 'cgit03', 'cgit1', 'cgit2', 'cgit3', 'ch', 'challenge', 'chance',
'channel', 'channels', 'chaos', 'charge', 'charlie', 'charlotte', 'charon',
'chase', 'chat', 'chat1', 'chat2', 'chats', 'chatserver', 'chcgil', 'che',
'check', 'checkout', 'checkpoint', 'checkrelay', 'checksrv', 'cheetah', 'chef',
'chef-01', 'chef-02', 'chef-03', 'chef-1', 'chef-2', 'chef-3', 'chef01',
'chef02', 'chef03', 'chef1', 'chef2', 'chef3', 'chelyabinsk',
'chelyabinsk-rnoc-rr02.backbone', 'chem', 'chemie', 'chemistry', 'cherry',
'chess', 'chi', 'chicago', 'chief', 'chimera', 'china', 'chinese', 'chip',
'chisinau', 'chocolate', 'chris', 'christian', 'christmas', 'chrome', 'chronos',
'chs', 'ci', 'cicril', 'cidr', 'cims', 'cinci', 'cincinnati', 'cinema', 'cip',
'cis', 'cisco', 'cisco-capwap-controller', 'cisco-lwapp-controller', 'cisco1',
'cisco2', 'cisl-murcia.cit', 'cit', 'citrix', 'city', 'civicrm', 'civil', 'cj',
'ck', 'cl', 'claims', 'clarizen', 'class', 'classes', 'classic', 'classified',
'classifieds', 'classroom', 'clearcase', 'clearquest', 'cleveland', 'cli',
'click', 'click1.mail', 'click3', 'clicks', 'clicktrack', 'client', 'clientes',
'clients', 'clientweb', 'clif', 'clifford.users', 'clinic', 'clip', 'clix',
'clock', 'clockingit', 'cloud', 'cloud1', 'cloud2', 'cloudflare-resolve-to',
'clsp', 'clt', 'clta', 'club', 'clubs', 'cluster', 'cluster1', 'clusters', 'cm',
'cma', 'cmail', 'cmc', 'cms', 'cms1', 'cms2', 'cn', 'cname', 'cnc', 'co',
'cobalt', 'cobra', 'coco', 'cocoa', 'cod', 'code', 'codebeamer', 'codendi',
'codesourcery', 'codetel', 'codeville', 'codex', 'cody', 'coffee', 'coldfusion',
'collab', 'collabtive', 'collection', 'collections', 'collector',
'collector-01', 'collector-02', 'collector-03', 'collector-1', 'collector-2',
'collector-3', 'collector01', 'collector02', 'collector03', 'collector1',
'collector2', 'collector3', 'college', 'colo', 'colombo', 'colombus',
'colorado', 'columbia', 'columbus', 'com', 'com-services-vip', 'comercial',
'comet', 'comet.webchat', 'comics', 'comm', 'comment', 'commerce',
'commerceserver', 'common', 'common-sw1', 'communication', 'communigate',
'community', 'company', 'compaq', 'compass', 'compras', 'compute-1', 'computer',
'computers', 'compuware', 'comunicacion', 'comunicare', 'comunicati',
'comunicazione', 'comunidad', 'con', 'conakry', 'concentrator', 'concordion',
'condor', 'conf', 'conference', 'conferences', 'conferencing', 'confidential',
'config', 'confluence', 'conformiq', 'connect', 'connect2', 'connecticut',
'consola', 'console', 'construction', 'construtor', 'consult', 'consultant',
'consultants', 'consulting', 'consumer', 'contact', 'contacts', 'content',
'content2', 'contents', 'contest', 'contests', 'contracts', 'contribute',
'control', 'controller', 'controlpanel', 'convert', 'cook', 'cookie', 'cool',
'coop', 'copenhagen', 'coral', 'core', 'core0', 'core01', 'core1', 'core2',
'core3', 'cork', 'corona', 'corp', 'corp-eur', 'corpmail', 'corporate',
'correio', 'correo', 'correoweb', 'cortafuegos', 'cosmic', 'cosmos', 'couch',
'couch-01', 'couch-02', 'couch-03', 'couch-1', 'couch-2', 'couch-3', 'couch01',
'couch02', 'couch03', 'couch1', 'couch2', 'couch3', 'couchdb', 'couchdb-01',
'couchdb-02', 'couchdb-03', 'couchdb-1', 'couchdb-2', 'couchdb-3', 'couchdb01',
'couchdb02', 'couchdb03', 'couchdb1', 'couchdb2', 'couchdb3', 'cougar', 'count',
'counter', 'counterstrike', 'country', 'coupon', 'coupons', 'course', 'courses',
'cp', 'cp1', 'cp10', 'cp2', 'cp3', 'cp4', 'cp5', 'cp6', 'cp7', 'cp8', 'cp9',
'cpa', 'cpanel', 'cpe', 'cppunit', 'cps', 'cq', 'cr', 'craft', 'crawl', 'crazy',
'crc', 'create', 'creative', 'credit', 'crew', 'cricket', 'crime', 'critical',
'crl', 'crm', 'crm2', 'cronos', 'cross', 'crown', 'crs', 'cruise',
'cruisecontrol', 'crux', 'crystal', 'cs', 'cs1', 'cs2', 'csc', 'cse', 'csg',
'csi', 'csm', 'cso', 'csp', 'csr', 'csr11.net', 'csr12.net', 'csr21.net',
'csr31.net', 'css', 'ct', 'ctrl', 'ctx', 'cu', 'cuba', 'cube', 'cubictest',
'cuckoo', 'cuckoo-01', 'cuckoo-02', 'cuckoo-03', 'cuckoo-1', 'cuckoo-2',
'cuckoo-3', 'cuckoo01', 'cuckoo02', 'cuckoo03', 'cuckoo1', 'cuckoo2', 'cuckoo3',
'cucumber', 'cultura', 'culture', 'cunit', 'cupid', 'cursos', 'cust',
'cust-adsl', 'cust1', 'cust10', 'cust100', 'cust101', 'cust102', 'cust103',
'cust104', 'cust105', 'cust106', 'cust107', 'cust108', 'cust109', 'cust11',
'cust110', 'cust111', 'cust112', 'cust113', 'cust114', 'cust115', 'cust116',
'cust117', 'cust118', 'cust119', 'cust12', 'cust120', 'cust121', 'cust122',
'cust123', 'cust124', 'cust125', 'cust126', 'cust13', 'cust14', 'cust15',
'cust16', 'cust17', 'cust18', 'cust19', 'cust2', 'cust20', 'cust21', 'cust22',
'cust23', 'cust24', 'cust25', 'cust26', 'cust27', 'cust28', 'cust29', 'cust3',
'cust30', 'cust31', 'cust32', 'cust33', 'cust34', 'cust35', 'cust36', 'cust37',
'cust38', 'cust39', 'cust4', 'cust40', 'cust41', 'cust42', 'cust43', 'cust44',
'cust45', 'cust46', 'cust47', 'cust48', 'cust49', 'cust5', 'cust50', 'cust51',
'cust52', 'cust53', 'cust54', 'cust55', 'cust56', 'cust57', 'cust58', 'cust59',
'cust6', 'cust60', 'cust61', 'cust62', 'cust63', 'cust64', 'cust65', 'cust66',
'cust67', 'cust68', 'cust69', 'cust7', 'cust70', 'cust71', 'cust72', 'cust73',
'cust74', 'cust75', 'cust76', 'cust77', 'cust78', 'cust79', 'cust8', 'cust80',
'cust81', 'cust82', 'cust83', 'cust84', 'cust85', 'cust86', 'cust87', 'cust88',
'cust89', 'cust9', 'cust90', 'cust91', 'cust92', 'cust93', 'cust94', 'cust95',
'cust96', 'cust97', 'cust98', 'cust99', 'custom', 'customer', 'customers', 'cv',
'cvs', 'cvsnt', 'cw', 'cwa', 'cwc', 'cx', 'cy', 'cyber', 'cyclone', 'cyclops',
'cygnus', 'cz', 'd', 'd.ns.e', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'da',
'dag', 'daily', 'daisy', 'dakar', 'dallas', 'dam', 'damascus', 'dan', 'dance',
'daniel', 'dante', 'dar', 'darcs', 'dart', 'dartenium', 'darwin', 'das', 'dash',
'dashboard', 'data', 'data1', 'data2', 'database', 'database01', 'database02',
'database1', 'database2', 'databases', 'datacenter', 'datastore', 'date',
'dating', 'datos', 'dav', 'dav75.users', 'dave', 'david', 'davinci', 'db',
'db0', 'db01', 'db02', 'db1', 'db2', 'db3', 'db4', 'db5', 'db6', 'dbadmin',
'dbs', 'dc', 'dc1', 'dc2', 'dcc', 'dcp', 'dcvs', 'dd', 'dds', 'de', 'deaddrop',
'deaddrop-01', 'deaddrop-02', 'deaddrop-03', 'deaddrop-1', 'deaddrop-2',
'deaddrop-3', 'deaddrop01', 'deaddrop02', 'deaddrop03', 'deaddrop1',
'deaddrop2', 'deaddrop3', 'deal', 'dealer', 'dealers', 'deals', 'dean',
'debbugs', 'debian', 'debug', 'dec', 'deck', 'deck-01', 'deck-02', 'deck-03',
'deck-1', 'deck-2', 'deck-3', 'deck01', 'deck02', 'deck03', 'deck1', 'deck2',
'deck3', 'deco', 'ded', 'dedicated', 'deep', 'def', 'default', 'defender',
'defiant', 'deimos', 'delaware', 'deliver', 'delivery', 'delivery.a',
'delivery.b', 'dell', 'delphi', 'delta', 'delta1', 'demeter', 'demo', 'demo1',
'demo10', 'demo2', 'demo3', 'demo4', 'demo5', 'demo6', 'demo7', 'demo8',
'demon', 'demonstration', 'demos', 'demwunz.users', 'deneb', 'denis', 'dental',
'denver', 'deploy', 'depo', 'deportes', 'depot', 'des', 'desa', 'desarrollo',
'descargas', 'design', 'designer', 'desire', 'desk', 'desktop', 'destek',
'destiny', 'detroit', 'dev', 'dev-www', 'dev.m', 'dev.movie', 'dev.music',
'dev.news', 'dev.payment', 'dev.travel', 'dev.www', 'dev0', 'dev01', 'dev1',
'dev2', 'dev3', 'dev4', 'dev5', 'devel', 'develo', 'develop', 'developer',
'developers', 'development', 'device', 'devil', 'devserver', 'devsql',
'devtest', 'dexter', 'df', 'dh', 'dhaka', 'dhcp', 'dhcp-bl', 'dhcp-in',
'dhcp.pilsnet', 'dhcp.zmml', 'dhcp1', 'dhcp2', 'dhcp4', 'di', 'diablo', 'dial',
'dialer', 'dialin', 'dialuol', 'dialup', 'diamond', 'diana', 'diary',
'dictionary', 'diemthi', 'diendan', 'dieseltest', 'diet', 'digital',
'digitaltester', 'digitaltv', 'dilbert', 'dili', 'dino', 'dion', 'dione', 'dip',
'dip0', 'dir', 'dirac', 'direct', 'director', 'directorio', 'directory', 'dis',
'disc', 'disco', 'discover', 'discovery', 'discuss', 'discussion',
'discussions', 'disk', 'disney', 'dist', 'distract', 'distributer',
'distributers', 'divine', 'diy', 'dj', 'djibouti', 'dk', 'dl', 'dl1', 'dl2',
'dls', 'dm', 'dmail', 'dms', 'dmz', 'dmz1', 'dn', 'dnews', 'dnn', 'dns',
'dns-2', 'dns0', 'dns01', 'dns02', 'dns1', 'dns11', 'dns12', 'dns2', 'dns3',
'dns4', 'dns5', 'dns6', 'dns7', 'dns8', 'dnstest', 'dnswl', 'do', 'doc',
'docker', 'docker-01', 'docker-02', 'docker-03', 'docker-1', 'docker-2',
'docker-3', 'docker01', 'docker02', 'docker03', 'docker1', 'docker2', 'docker3',
'docs', 'doctor', 'document', 'documentacion', 'documentation', 'documentos',
'documents', 'dodge', 'dodo', 'dog', 'doha', 'dolibarr', 'dolphin', 'dom',
'domain', 'domain-controller', 'domain2', 'domaincontroller', 'domaincp',
'domaindnszones', 'domains', 'dominio', 'domino', 'dominoweb', 'domolink',
'domreg', 'don', 'donald', 'donate', 'doom', 'door', 'doors', 'dora', 'doska',
'dot', 'dotproject', 'douglas', 'down', 'download', 'download1', 'download2',
'downloads', 'downtown', 'dp', 'dps', 'dr', 'draco', 'dradis', 'dradis-01',
'dradis-02', 'dradis-03', 'dradis-1', 'dradis-2', 'dradis-3', 'dradis01',
'dradis02', 'dradis03', 'dradis1', 'dradis2', 'dradis3', 'dragon',
'dragonflybsd', 'dream', 'dreamer', 'dreams', 'drive', 'driver', 'drivers',
'drm', 'dropbox', 'drupal', 'drweb', 'ds', 'ds1', 'ds2', 'dsasa', 'dsl',
'dsl-w', 'dsp', 'dspace', 'dss', 'dt', 'dtc', 'dti', 'dubious.users', 'dublin',
'duke', 'dummy', 'dune', 'durable', 'dushanbe', 'duxqa', 'dv', 'dv1', 'dvd',
'dvr', 'dw', 'dweb', 'dy', 'dyn', 'dynamic', 'dynamicip', 'dynamics', 'dynip',
'dz', 'e', 'e-com', 'e-commerce', 'e-learning', 'e.ns.e', 'e0', 'e1', 'e2',
'e3', 'ea', 'eaccess', 'ead', 'eagle', 'earth', 'eas', 'east', 'easy', 'eate4',
'eate4-cert', 'ebay', 'ebill', 'ebiz', 'ebook', 'ebooks', 'ec', 'ecard', 'ecc',
'ece', 'echo', 'eclipse', 'ecm', 'eco', 'ecology', 'ecom', 'ecommerce', 'econ',
'ecs', 'ed', 'eden', 'edgar', 'edge', 'edge1', 'edge2', 'edi', 'edinburgh',
'edison', 'edit', 'editor', 'edm', 'edocs', 'edu', 'education', 'eduroam',
'edward', 'ee', 'eee', 'ef', 'eg', 'egitim', 'egroupware', 'egypt', 'eh', 'ehr',
'einstein', 'eip', 'eis', 'ejemplo', 'ejournal', 'ekaterinburg', 'ekb',
'ekonomi', 'el', 'elastic', 'elastic-01', 'elastic-02', 'elastic-03',
'elastic-1', 'elastic-2', 'elastic-3', 'elastic01', 'elastic02', 'elastic03',
'elastic1', 'elastic2', 'elastic3', 'elasticsearch', 'elasticsearch-01',
'elasticsearch-02', 'elasticsearch-03', 'elasticsearch-1', 'elasticsearch-2',
'elasticsearch-3', 'elasticsearch01', 'elasticsearch02', 'elasticsearch03',
'elasticsearch1', 'elasticsearch2', 'elasticsearch3', 'elearn', 'elearning',
'election', 'elections', 'electronics', 'elephant', 'elib', 'elibrary', 'elite',
'elmo', 'eload', 'elpaso', 'elvior', 'elvis', 'em', 'email', 'email2',
'emarketing', 'embratel', 'emerald', 'emergency', 'emhril', 'emkt', 'emma',
'empire', 'empirix', 'empleo', 'emploi', 'employees', 'empresa', 'empresas',
'ems', 'en', 'enable', 'encuestas', 'endeavour', 'energy', 'enet1', 'enews',
'eng', 'eng01', 'eng1', 'engine', 'engineer', 'engineering', 'english',
'enigma', 'enquete', 'enrutador', 'ent', 'enter', 'enterprise', 'entertainment',
'eo', 'eonet', 'eos', 'ep', 'epaper', 'epay', 'epesi', 'epesibim', 'epm',
'eposta', 'eprints', 'eproc', 'epsilon', 'er', 'era', 'eric', 'eris', 'ernie',
'eros', 'erp', 'err', 'error', 'es', 'es-01', 'es-02', 'es-03', 'es-1', 'es-2',
'es-3', 'es01', 'es02', 'es03', 'es1', 'es2', 'es3', 'esd', 'eservices',
'eshop', 'esm', 'esp', 'espanol', 'ess', 'est', 'estadisticas', 'estore', 'esx',
'esx1', 'esx2', 'esx3', 'et', 'eta', 'etb', 'etc', 'eternity', 'etester',
'eth0', 'etools', 'eu', 'eu.pool', 'euclid', 'eugene', 'eur', 'eureka', 'euro',
'euro2012', 'europa', 'europe', 'ev', 'eva', 'eval', 'eve', 'event',
'eventlogger', 'eventlogger-01', 'eventlogger-02', 'eventlogger-03',
'eventlogger-1', 'eventlogger-2', 'eventlogger-3', 'eventlogger01',
'eventlogger02', 'eventlogger03', 'eventlogger1', 'eventlogger2',
'eventlogger3', 'eventos', 'events', 'eventum', 'everest', 'everything', 'evo',
'evolution', 'ex', 'exam', 'example', 'examples', 'exams', 'excel', 'exch',
'exchange', 'exchange-imap.its', 'exchbhlan3', 'exchbhlan5', 'exec', 'exim',
'exit', 'exmail', 'exodus', 'exp', 'expert', 'experts', 'expo', 'export',
'express', 'ext', 'ext.webchat', 'extern', 'external', 'extra', 'extranet',
'extranet2', 'extranets', 'extras', 'extreme', 'eye', 'ez', 'ezproxy', 'f',
'f.ns.e', 'f1', 'f2', 'f3', 'f5', 'fa', 'face', 'facebook', 'factory',
'faculty', 'faith', 'falcon', 'fall', 'familiar', 'family', 'fan', 'fantasy',
'faq', 'faraday', 'farm', 'fashion', 'fast', 'faststats', 'fasttrack', 'fax',
'fb', 'fbapps', 'fbl', 'fbx', 'fc', 'fd', 'fdc', 'fe', 'fe1', 'fe2', 'fedora',
'fedoracore', 'feed', 'feedback', 'feeds', 'felix', 'feng', 'fenix',
'ferrari.fortwayne.com.', 'festival', 'ff', 'fh', 'fi', 'fibertel', 'field',
'file', 'files', 'files2', 'fileserv', 'fileserver', 'fileshare', 'filestore',
'film', 'filme', 'filter', 'fin', 'finance', 'find', 'finger', 'fiona', 'fios',
'fire', 'firefly', 'firewall', 'firma', 'firmware', 'firmy', 'first', 'fis',
'fish', 'fisher', 'fisto', 'fitness', 'fix', 'fixes', 'fj', 'fk', 'fl', 'flash',
'flex', 'florence', 'florida', 'flow', 'flower', 'flowers', 'flr-all',
'flumotion', 'flv', 'fly', 'flyspray', 'fm', 'fms', 'fo', 'focus', 'fogbugz',
'foo', 'foobar', 'food', 'football', 'ford', 'forest', 'forestdnszones',
'forex', 'forge', 'form', 'formacion', 'forms', 'fornax', 'foro', 'foros',
'fortuna', 'fortune', 'fortworth', 'forum', 'forum1', 'forum2', 'forums',
'forumtest', 'forward', 'fossil', 'foto', 'fotogaleri', 'fotos', 'foundation',
'foundry', 'fox', 'foxtrot', 'fp', 'fr', 'france', 'franchise', 'frank',
'frankenstein', 'franklin', 'fred', 'freddy', 'free', 'freebies', 'freebsd',
'freebsd0', 'freebsd01', 'freebsd02', 'freebsd1', 'freebsd2', 'freecast',
'freedom', 'freemaildomains', 'freetown', 'freeware', 'french', 'fresh',
'fresno', 'friend', 'friends', 'frodo', 'frog', 'froglogic', 'frokca', 'fromwl',
'front', 'front1', 'front2', 'frontdesk', 'frontend', 'fs', 'fs1', 'fs2',
'fsimg', 'fsp', 'ft', 'ftas', 'ftd', 'ftp', 'ftp-', 'ftp-eu', 'ftp.blog',
'ftp.dev', 'ftp.forum', 'ftp.m', 'ftp.test', 'ftp0', 'ftp01', 'ftp1', 'ftp2',
'ftp3', 'ftp4', 'ftp5', 'ftp6', 'ftp_', 'ftpd', 'ftps', 'ftpserver', 'ftptest',
'fuji', 'fun', 'functional', 'functionaltester', 'fund', 'fusion', 'futbol',
'future', 'fw', 'fw-1', 'fw1', 'fw2', 'fwallow', 'fwd', 'fwptt', 'fwsm',
'fwsm0', 'fwsm01', 'fwsm1', 'fx', 'fxp', 'fz', 'g', 'g1', 'g2', 'g3', 'ga',
'gaborone', 'gaia', 'gala', 'galaxy', 'galeria', 'galerias', 'galileo',
'galleries', 'gallery', 'galway', 'game', 'game1', 'gameinfo', 'gamer',
'gamers', 'games', 'gamma', 'gandalf', 'ganymede', 'gapps', 'garfield', 'gas',
'gate', 'gate2', 'gatekeeper', 'gateway', 'gateway1', 'gateway2', 'gauss',
'gay', 'gazeta', 'gb', 'gc', 'gc._msdcs', 'gcc', 'gd', 'ge', 'ged', 'gemini',
'general', 'genericrev', 'genesis', 'geniesys', 'genietcms', 'genius', 'gentoo',
'geo', 'geoip', 'george', 'georgetown', 'georgia', 'german', 'germany',
'gestion', 'get', 'gf', 'gfx', 'gg', 'gh', 'ghost', 'gi', 'gift', 'gifts',
'giga', 'gilford', 'girls', 'girocco', 'girocco-01', 'girocco-02', 'girocco-03',
'girocco-1', 'girocco-2', 'girocco-3', 'girocco01', 'girocco02', 'girocco03',
'girocco1', 'girocco2', 'girocco3', 'gis', 'git', 'gitalist', 'gitalist-01',
'gitalist-02', 'gitalist-03', 'gitalist-1', 'gitalist-2', 'gitalist-3',
'gitalist01', 'gitalist02', 'gitalist03', 'gitalist1', 'gitalist2', 'gitalist3',
'github', 'github-01', 'github-02', 'github-03', 'github-1', 'github-2',
'github-3', 'github01', 'github02', 'github03', 'github1', 'github2', 'github3',
'gitlab', 'gitlab-01', 'gitlab-02', 'gitlab-03', 'gitlab-1', 'gitlab-2',
'gitlab-3', 'gitlab01', 'gitlab02', 'gitlab03', 'gitlab1', 'gitlab2', 'gitlab3',
'gitorious', 'gitorious-01', 'gitorious-02', 'gitorious-03', 'gitorious-1',
'gitorious-2', 'gitorious-3', 'gitorious01', 'gitorious02', 'gitorious03',
'gitorious1', 'gitorious2', 'gitorious3', 'gitweb', 'gitweb-01', 'gitweb-02',
'gitweb-03', 'gitweb-1', 'gitweb-2', 'gitweb-3', 'gitweb01', 'gitweb02',
'gitweb03', 'gitweb1', 'gitweb2', 'gitweb3', 'gizmo', 'gk', 'gl', 'glass',
'glasscubes', 'glendale', 'global', 'gloria', 'glpi', 'gm', 'gmail', 'gms',
'gn', 'gnats', 'go', 'gobbit.users', 'god', 'gogo', 'gold', 'golden',
'goldmine', 'golf', 'gollum', 'gonzo', 'good', 'goodluck', 'goofy', 'google',
'gopher', 'goplan', 'gordon', 'goto', 'gourmet', 'gov', 'govyty', 'gp', 'gprs',
'gps', 'gq', 'gr', 'grace', 'graduate', 'grand', 'graph', 'graphics',
'graphite', 'graphite-01', 'graphite-02', 'graphite-03', 'graphite-1',
'graphite-2', 'graphite-3', 'graphite01', 'graphite02', 'graphite03',
'graphite1', 'graphite2', 'graphite3', 'green', 'greetings', 'grid', 'grinder',
'group', 'groups', 'groupware', 'groupwise', 'gry', 'gs', 'gsa', 'gsgou.users',
'gsm', 'gsp', 'gsx', 'gt', 'gta', 'gtcust', 'gu', 'guardian', 'guatemala',
'guest', 'guide', 'guides', 'guitar', 'gurock', 'guru', 'gvt', 'gw', 'gw-ndh',
'gw1', 'gw2', 'gw3', 'gx', 'gy', 'gye', 'gz', 'gzs', 'h', 'h1', 'h2', 'h3',
'h4', 'h5', 'ha', 'ha.pool', 'haber', 'hack', 'hacker', 'hades', 'hadoop',
'hadoop-01', 'hadoop-02', 'hadoop-03', 'hadoop-1', 'hadoop-2', 'hadoop-3',
'hadoop01', 'hadoop02', 'hadoop03', 'hadoop1', 'hadoop2', 'hadoop3', 'haha',
'hal', 'halflife', 'hammerhead', 'hammerora', 'hamster', 'hanoi', 'hans',
'happy', 'haproxy', 'haproxy-01', 'haproxy-02', 'haproxy-03', 'haproxy-1',
'haproxy-2', 'haproxy-3', 'haproxy01', 'haproxy02', 'haproxy03', 'haproxy1',
'haproxy2', 'haproxy3', 'harare', 'hardcore', 'hardware', 'harmony', 'harry',
'harvest', 'hasp', 'hathor', 'havana', 'hawaii', 'hawk', 'hb', 'hc', 'hcm',
'hd', 'he', 'health', 'healthcare', 'heart', 'heaven', 'hefesto', 'helena',
'helios', 'helium', 'helix', 'hello', 'helm', 'helomatch', 'help', 'helpdesk',
'helponline', 'helsinki', 'henry', 'hera', 'heracles', 'hercules', 'hermes',
'hestia', 'hfc', 'hfccourse.users', 'hfgfgf', 'hg', 'hgfgdf', 'hi', 'hidden',
'hidden-host', 'hideip', 'hideip-usa', 'highway', 'hinet-ip', 'hiphop',
'hirlevel', 'history', 'hit', 'hk', 'hkcable', 'hkps.pool', 'hl', 'hlrn', 'hm',
'hn', 'hobbes', 'hobbit', 'hobby', 'hokkaido', 'holiday', 'holly', 'hollywood',
'home', 'home1', 'home2', 'homebase', 'homer', 'homerun', 'homes',
'homologacao', 'honey', 'honeypot', 'hongkong', 'honiara', 'honkkong',
'honolulu', 'hope', 'horizon', 'hornet', 'horo', 'horse', 'horus', 'hospital',
'host', 'host1', 'host10', 'host11', 'host12', 'host13', 'host14', 'host15',
'host16', 'host17', 'host18', 'host19', 'host2', 'host20', 'host21', 'host2123',
'host22', 'host23', 'host26', 'host3', 'host4', 'host5', 'host6', 'host7',
'host8', 'host9', 'hosted', 'hosting', 'hosting1', 'hosting2', 'hosting3',
'hostkarma', 'hot', 'hotel', 'hotels', 'hotjobs', 'hotline', 'hotspot', 'house',
'housing', 'houstin', 'houston', 'howard', 'howto', 'hp', 'hp-ux', 'hpc',
'hpov', 'hpux', 'hq', 'hr', 'hrlntx', 'hrm', 'hs', 'hsia', 'hstntx', 'hsv',
'ht', 'html', 'html5', 'htmlunit', 'http', 'https', 'httpunit', 'hu', 'hub',
'huddle', 'hudson', 'hudson-01', 'hudson-02', 'hudson-03', 'hudson-1',
'hudson-2', 'hudson-3', 'hudson01', 'hudson02', 'hudson03', 'hudson1',
'hudson2', 'hudson3', 'human', 'humanresources', 'humor', 'hunter', 'hwmaint',
'hybrid', 'hydra', 'hydrogen', 'hyper', 'hyperion', 'hypernova', 'hyperoffice',
'hyundai', 'i', 'i0.comet.webchat', 'i1', 'i1.comet.webchat', 'i2',
'i2.comet.webchat', 'i3', 'i3.comet.webchat', 'i4', 'i4.comet.webchat', 'i5',
'i5.comet.webchat', 'i6.comet.webchat', 'i7.comet.webchat', 'i8.comet.webchat',
'i9.comet.webchat', 'ia', 'ias', 'ib', 'ibank', 'ibm', 'ibmdb', 'ic', 'icare',
'ice', 'icecast', 'icm', 'icon', 'icq', 'ics', 'ict', 'id', 'ida', 'idaho',
'idb', 'idc', 'idea', 'ideas', 'identity', 'idm', 'idp', 'ids', 'ie', 'iern',
'if', 'ifolder', 'ig', 'igk', 'igor', 'iis', 'ikiwiki', 'il', 'ilias',
'illinois', 'ilmi', 'ils', 'im', 'im1', 'im2', 'im3', 'im4', 'image', 'image1',
'image2', 'imagenes', 'images', 'images0', 'images1', 'images2', 'images3',
'images4', 'images5', 'images6', 'images7', 'images8', 'imagine', 'imail',
'imap', 'imap1', 'imap2', 'imap3', 'imap3d', 'imap4', 'imapd', 'imaps', 'imc',
'img', 'img0', 'img01', 'img02', 'img1', 'img10', 'img11', 'img13', 'img2',
'img3', 'img4', 'img5', 'img6', 'img7', 'img8', 'img9', 'imgs', 'imode', 'imp',
'impact', 'import', 'impsat', 'ims', 'in', 'in-addr', 'inbound', 'inbox', 'inc',
'incisif', 'include', 'incoming', 'indefero', 'indefero-01', 'indefero-02',
'indefero-03', 'indefero-1', 'indefero-2', 'indefero-3', 'indefero01',
'indefero02', 'indefero03', 'indefero1', 'indefero2', 'indefero3', 'index',
'india', 'indiana', 'indianapolis', 'indigo', 'indonesia', 'inet', 'inf',
'infinity', 'inflectra', 'info', 'informatica', 'information', 'informix',
'informup', 'infoweb', 'innovation', 'inside', 'insight', 'install',
'insurance', 'int', 'integration', 'intelignet', 'inter', 'interactive',
'interface', 'intern', 'internal', 'internalhost', 'international', 'internet',
'interno', 'internode', 'intl', 'intra', 'intranet', 'intranet2', 'invalid',
'inventory', 'invest', 'investor', 'investors', 'invia', 'invio', 'invoice',
'io', 'ios', 'iota', 'iowa', 'ip', 'ip-us', 'ip-usa', 'ip1', 'ip2', 'ip215',
'ip6', 'ipad', 'ipc', 'ipcom', 'iphone', 'iplanet', 'iplsin', 'ipltin',
'ipmonitor', 'iprimus', 'iproxy', 'ips', 'ipsec', 'ipsec-gw', 'ipsp', 'ipt',
'iptv', 'ipv4', 'ipv4.pool', 'ipv6', 'ipv6.teredo', 'iq', 'ir', 'irc', 'ircd',
'ircserver', 'ireland', 'iris', 'irix', 'irkutsk', 'iron', 'ironport', 'irvine',
'irving', 'irvnca', 'is', 'isa', 'isaserv', 'isaserver', 'isis', 'islam',
'islamabad', 'ism', 'iso', 'isp', 'isp-caledon.cit', 'isphosts', 'israel',
'iss', 'issuenet', 'issues', 'ist', 'istun', 'isupport', 'isync', 'it',
'italia', 'italy', 'itc', 'itcampus', 'its', 'itsupport', 'itv', 'iuyuy',
'iuyuyt', 'ivan', 'ivanovo', 'ivr', 'ix', 'ixhash', 'j', 'ja', 'jabber', 'jack',
'jackson', 'jade', 'jadeliquid', 'jaguar', 'jakarta', 'jake', 'james', 'jan',
'janus', 'japan', 'japanese', 'jason', 'jasper', 'java', 'jax', 'jazz', 'jb',
'jbehave', 'jboss', 'jc', 'jcrawler', 'jd', 'je', 'jedi', 'jeff', 'jemmy',
'jenkins', 'jenkins-01', 'jenkins-02', 'jenkins-03', 'jenkins-1', 'jenkins-2',
'jenkins-3', 'jenkins01', 'jenkins02', 'jenkins03', 'jenkins1', 'jenkins101',
'jenkins2', 'jenkins3', 'jerry', 'jewel', 'jewelry', 'jf', 'jfunc', 'jg',
'jgdw', 'jim', 'jira', 'jira-01', 'jira-02', 'jira-03', 'jira-1', 'jira-2',
'jira-3', 'jira01', 'jira02', 'jira03', 'jira1', 'jira2', 'jira3', 'jite',
'jjc', 'jl', 'jm', 'jmeter', 'jo', 'job', 'jobb', 'jobs', 'jocuri', 'joe',
'john', 'join', 'jojo', 'joomla', 'joomla-01', 'joomla-02', 'joomla-03',
'joomla-1', 'joomla-2', 'joomla-3', 'joomla01', 'joomla02', 'joomla03',
'joomla1', 'joomla2', 'joomla3', 'jose', 'jotbug', 'journal', 'journals',
'journyx', 'joyce', 'jp', 'jpkc', 'jrun', 'js', 'jsc', 'jtest', 'jtrack',
'juba', 'juegos', 'juliet', 'juliette', 'jump', 'junior', 'juniper', 'junit',
'juno', 'jupiter', 'just', 'jw', 'jwc', 'jwebunit', 'jwgl', 'jx', 'jy', 'k',
'k12', 'k2', 'kabul', 'kalender', 'kaliningrad', 'kaluga', 'kampala', 'kansas',
'kansascity', 'kappa', 'karen', 'karma', 'katalog', 'kathmandu', 'kayako',
'kazan', 'kb', 'kbtelecom', 'kc', 'ke', 'keith', 'kelly', 'kemerovo', 'ken',
'kenny', 'kent', 'kentucky', 'kepler', 'kerberos', 'kevin', 'key', 'keynote',
'keys', 'kforge', 'kg', 'kh', 'khartoum', 'khjghg', 'ki', 'kid', 'kids', 'kiev',
'kigali', 'killer', 'kilo', 'kim', 'king', 'kingston', 'kingstown', 'kino',
'kinshasa', 'kiosk', 'kira', 'kirk', 'kirov', 'kiss', 'kit', 'kita', 'kitchen',
'kiwi', 'kjc', 'kk', 'kkoop', 'klmzmi', 'km', 'kms', 'kn', 'knowledge',
'knowledgebase', 'knoxville', 'ko', 'koe', 'koko', 'kong', 'konkurs', 'korea',
'kp', 'kr', 'kraken', 'krasnodar', 'krasnoyarsk', 'kris', 'kronos', 'ks',
'ksc2mo', 'kt', 'kuala', 'kultur', 'kurgan', 'kursk', 'kuwait', 'kvm', 'kvm1',
'kvm2', 'kvm3', 'kvm4', 'kw', 'ky', 'kyc', 'kz', 'l', 'l2tp-us', 'la', 'la2',
'lab', 'lab1', 'labor', 'laboratories', 'laboratory', 'labs', 'lady', 'laguna',
'lala', 'lambda', 'lamour', 'lamp', 'lan', 'lancaster', 'land', 'landing',
'laptop', 'laserjet', 'lasvegas', 'launch', 'launchpad', 'laura', 'law', 'lb',
'lb1', 'lb2', 'lbtest', 'lc', 'ld', 'ldap', 'ldap1', 'ldap2', 'ldap3', 'lds',
'lead', 'leads', 'learn', 'learning', 'leda', 'legacy', 'legal', 'legend',
'lego', 'lemon', 'leo', 'leon', 'leonardo', 'leopard', 'leto', 'letter',
'lewis', 'lex', 'lft', 'lg', 'li', 'lib', 'liberty', 'liberum', 'libguides',
'libproxy', 'libra', 'library', 'libresource', 'libreville', 'license', 'lider',
'life', 'lifestyle', 'light', 'lightning', 'like', 'lilongwe', 'lily', 'lima',
'lime', 'lina', 'lincoln', 'line', 'link', 'links', 'linux', 'linux0',
'linux01', 'linux02', 'linux1', 'linux2', 'lion', 'lions', 'lipetsk',
'liquidplanner', 'liquidtest', 'lisa', 'lisbon', 'list', 'lista', 'listas',
'listes', 'listman', 'lists', 'listserv', 'listserver', 'lite', 'lithium',
'little', 'live', 'live2', 'livechat', 'livehelp', 'livestream', 'livnmi',
'ljubljana', 'lk', 'lkjkui', 'lkljk', 'll', 'lm', 'lms', 'ln', 'lnk', 'lo0',
'load', 'loadbalancer', 'loadrunner', 'local', 'local.api', 'localhost', 'loco',
'log', 'log0', 'log01', 'log02', 'log1', 'log2', 'logfile', 'logfiles',
'logger', 'logging', 'loghost', 'login', 'logistics', 'logo', 'logon', 'logos',
'logs', 'loja', 'loki', 'lol', 'lolo', 'lome', 'london', 'longbeach',
'loopback', 'losangeles', 'lotto', 'lotus', 'louisiana', 'love', 'lp', 'lp1',
'lp2', 'lpse', 'lr', 'ls', 'lsan03', 'lt', 'ltrkar', 'lu', 'luanda', 'lucky',
'lucy', 'luigi', 'luke', 'lulu', 'luna', 'lusaka', 'lux', 'luxembourg',
'luxury', 'lv', 'lw', 'lx', 'ly', 'lync', 'lyncaccess', 'lyncav',
'lyncdiscover', 'lyncdiscoverinternal', 'lyncedge', 'lyncweb', 'lynx', 'lyris',
'm', 'm.dev', 'm.plb1', 'm.plb2', 'm.slb1', 'm.slb2', 'm.stage', 'm.test', 'm0',
'm0n0', 'm0n0wall', 'm1', 'm10', 'm11', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7',
'm8', 'm9', 'ma', 'maa', 'mac', 'mac1', 'mac10', 'mac11', 'mac2', 'mac3',
'mac4', 'mac5', 'macduff', 'mach', 'macintosh', 'made.by', 'madrid', 'maestro',
'mag', 'magazin', 'magazine', 'magento', 'magic', 'magnetic', 'magnolia',
'maia', 'mail', 'mail-out', 'mail-relay', 'mail.blog', 'mail.forum', 'mail.m',
'mail.test', 'mail0', 'mail01', 'mail02', 'mail03', 'mail04', 'mail05',
'mail07', 'mail1', 'mail1.mail', 'mail10', 'mail11', 'mail12', 'mail13',
'mail14', 'mail15', 'mail17', 'mail2', 'mail2.mail', 'mail20', 'mail21',
'mail3', 'mail3.mail', 'mail4', 'mail4.mail', 'mail5', 'mail5.mail', 'mail6',
'mail6.mail', 'mail7', 'mail7.mail', 'mail8', 'mail9', 'mailadmin', 'mailbox',
'mailer', 'mailer1', 'mailer2', 'mailers', 'mailfilter', 'mailgate',
'mailgate2', 'mailgateway', 'mailgw', 'mailgw1', 'mailgw2', 'mailhost',
'mailhub', 'mailin', 'mailing', 'mailings', 'maillist', 'maillists', 'mailman',
'mailold', 'mailout', 'mailrelay', 'mailroom', 'mails', 'mailserv',
'mailserver', 'mailserver2', 'mailservers', 'mailsite', 'mailsrv', 'mailtest',
'mailx', 'main', 'maine', 'maint', 'maintenance', 'majuro', 'malabo', 'male',
'mall', 'malotedigital', 'mama', 'man', 'manage', 'managedomain', 'management',
'manager', 'managers', 'managua', 'manama', 'mandrake', 'mandriva', 'manga',
'mango', 'manila', 'mantis', 'mantisbt', 'manual', 'manuals', 'manufacturing',
'map', 'mapas', 'mapi', 'maple', 'maps', 'maputo', 'marathon', 'marc', 'marco',
'marcus', 'marge', 'maria', 'marina', 'mario', 'mark', 'market', 'marketing',
'marketplace', 'mars', 'marte', 'martin', 'marvin', 'mary', 'maryland', 'mas',
'maseru', 'massachusetts', 'master', 'matchware', 'math', 'maths', 'matrix',
'matrixstats', 'matt', 'maven', 'maverick', 'max', 'maxim', 'maxonline',
'maxwell', 'maya', 'mayday', 'mb', 'mb2', 'mba', 'mbabana', 'mbox', 'mbt', 'mc',
'mcast', 'mcc', 'mccoy', 'mci', 'mco', 'mcp', 'mcs', 'mcu', 'md', 'mdaemon',
'mdev', 'mdm', 'mds', 'me', 'mec', 'mech', 'med', 'media', 'media1', 'media2',
'mediakit', 'medias', 'mediaserver', 'medical', 'medicine', 'medusa', 'meerkat',
'meerkat-01', 'meerkat-02', 'meerkat-03', 'meerkat-1', 'meerkat-2', 'meerkat-3',
'meerkat01', 'meerkat02', 'meerkat03', 'meerkat1', 'meerkat2', 'meerkat3',
'meet', 'meeting', 'meetings', 'mega', 'megaegg', 'megared', 'mel', 'melbourne',
'melekeok', 'melody', 'mem', 'member', 'member2', 'members', 'members2',
'membership', 'memcache', 'memcache-01', 'memcache-02', 'memcache-03',
'memcache-1', 'memcache-2', 'memcache-3', 'memcache01', 'memcache02',
'memcache03', 'memcache1', 'memcache2', 'memcache3', 'memcached',
'memcached-01', 'memcached-02', 'memcached-03', 'memcached-1', 'memcached-2',
'memcached-3', 'memcached01', 'memcached02', 'memcached03', 'memcached1',
'memcached2', 'memcached3', 'meme', 'memphis', 'men', 'mercedes', 'mercure',
'mercurial', 'mercurio', 'mercury', 'merlin', 'mes', 'mesh', 'message',
'messagemagic', 'messages', 'messaging', 'messenger', 'meta', 'metal', 'meteo',
'meteor', 'metis', 'metrics', 'metro', 'mexico', 'mf', 'mg', 'mgc', 'mgk',
'mgmt', 'mh', 'mi', 'mia', 'miamfl', 'miami', 'mic', 'michael', 'michelle',
'michigan', 'mickey', 'micro', 'microsite', 'microsoft', 'mid', 'midwest',
'mig', 'migration', 'mike', 'miki', 'military', 'milk', 'millenium',
'milwaukee', 'milwwi', 'mina', 'mine', 'minecraft', 'minerva', 'mingle', 'mini',
'minneapolis', 'minnesota', 'minsk', 'mint', 'mir', 'mira', 'mirage', 'mirror',
'mirror1', 'mirror2', 'mirrors', 'mis', 'miss', 'mississippi', 'missouri',
'mitsubishi', 'mix', 'mjurr', 'mk', 'mks', 'mksintegrity', 'mkt', 'mkuu', 'ml',
'mlm', 'mlr-all', 'mls', 'mm', 'mmc', 'mmm', 'mms', 'mn', 'mngt', 'mo', 'mob',
'mobi', 'mobil', 'mobile', 'mobile1', 'mobile2', 'mobilemail', 'mobileonline',
'mobility', 'mod', 'moda', 'model', 'models', 'modem', 'moe', 'mogadishu',
'mojo', 'molly', 'mom', 'mon', 'monaco', 'money', 'mongo', 'mongo-01',
'mongo-02', 'mongo-03', 'mongo-1', 'mongo-2', 'mongo-3', 'mongo01', 'mongo02',
'mongo03', 'mongo1', 'mongo2', 'mongo3', 'mongodb', 'mongodb-01', 'mongodb-02',
'mongodb-03', 'mongodb-1', 'mongodb-2', 'mongodb-3', 'mongodb01', 'mongodb02',
'mongodb03', 'mongodb1', 'mongodb2', 'mongodb3', 'monit', 'monitor', 'monitor1',
'monitor2', 'monitoring', 'monkey', 'monotone', 'monowall', 'monrovia',
'monster', 'montana', 'montevideo', 'monty', 'moo', 'moodle', 'moodle2', 'moon',
'moroni', 'moscow', 'moss', 'mother', 'moto', 'motor', 'move', 'movie',
'movies', 'movil', 'mozart', 'mp', 'mp1', 'mp3', 'mpa', 'mpeg', 'mpg', 'mpls',
'mproxy', 'mps', 'mq', 'mr', 'mradm.letter', 'mrt', 'mrtg', 'mrtg2', 'ms',
'ms-exchange', 'ms-sql', 'ms1', 'ms2', 'msa', 'mse', 'msexchange', 'msg',
'msgrs.webchat', 'msk', 'msn', 'msn-smtp-out', 'msp', 'mssnks', 'mssql',
'mssql0', 'mssql01', 'mssql1', 'mssql2', 'mst', 'mstun', 'msy', 'mt', 'mta',
'mta1', 'mta2', 'mta3', 'mta4', 'mta5', 'mtest', 'mtnl', 'mts', 'mtu', 'mu',
'multi', 'multimedia', 'mumbai', 'mumble', 'munin', 'murmansk', 'muscat',
'museum', 'mushroom', 'music', 'musica', 'musik', 'mustang', 'mv', 'mvn', 'mw',
'mweb', 'mx', 'mx0', 'mx01', 'mx02', 'mx03', 'mx04', 'mx1', 'mx10', 'mx11',
'mx12', 'mx2', 'mx3', 'mx4', 'mx5', 'mx6', 'mx7', 'mx8', 'mxbackup2', 'mxs',
'my', 'myaccount', 'myadmin', 'myfiles', 'myhome', 'mymail', 'mypage', 'myshop',
'mysite', 'mysites', 'myspace', 'mysql', 'mysql-01', 'mysql-02', 'mysql-03',
'mysql-1', 'mysql-2', 'mysql-3', 'mysql0', 'mysql01', 'mysql02', 'mysql03',
'mysql1', 'mysql2', 'mysql3', 'mysql4', 'mysql5', 'mysql6', 'mysql7', 'mysql8',
'mysqladmin', 'mytest', 'myweb', 'mz', 'n', 'n1', 'n2', 'na', 'na.pool',
'nagano', 'nagios', 'nairobi', 'nam', 'name', 'names', 'nameserv', 'nameserver',
'nana', 'nano', 'naruto', 'nas', 'nas1', 'nas2', 'nashville', 'nassau', 'nat',
'natasha', 'natural', 'nature', 'nautilus', 'nav', 'navi', 'navision', 'nb',
'nc', 'ncc', 'ncs', 'nd', 'ndjamena', 'nds', 'ne', 'nebraska', 'nebula',
'nelson', 'nemesis', 'nemo', 'neo', 'neon', 'neptun', 'neptune', 'neptuno',
'nero', 'net', 'netapp', 'netbsd', 'netdata', 'netflow', 'netgear', 'netlab',
'netmail', 'netmeeting', 'netmon', 'netscaler', 'netscreen', 'netstats',
'netvision', 'netware', 'network', 'neu', 'nevada', 'new', 'new1', 'new2',
'newforum', 'newhampshire', 'newjersey', 'newmail', 'newmexico', 'neworleans',
'news', 'news1', 'news2', 'newserver', 'newsfeed', 'newsfeeds', 'newsgroups',
'newsite', 'newsletter', 'newsletters', 'newsroom', 'newton', 'newweb',
'newyork', 'newzealand', 'next', 'nexus', 'nf', 'nfs', 'nfs01.jc', 'ng',
'nginx', 'nh', 'nhko1111', 'ni', 'niamey', 'nic', 'nice', 'nicolas', 'nicosia',
'nieuwsbrief', 'nigeria', 'night', 'nike', 'nimbus', 'ninja', 'nis', 'nissan',
'nix', 'nj', 'nl', 'nm', 'nms', 'nn', 'nnov', 'nntp', 'no', 'no-dns',
'no-dns-yet', 'noah', 'nobl', 'noc', 'nod', 'nod32', 'node', 'node1', 'node2',
'nokia', 'nombres', 'noname', 'nora', 'north', 'northcarolina', 'northdakota',
'northeast', 'northwest', 'not-set-yet', 'notebook', 'notes', 'nothing',
'noticias', 'notify', 'nouakchott', 'nova', 'novell', 'november', 'novo',
'novosibirsk', 'now', 'np', 'npm', 'npm-01', 'npm-02', 'npm-03', 'npm-1',
'npm-2', 'npm-3', 'npm-registry', 'npm01', 'npm02', 'npm03', 'npm1', 'npm2',
'npm3', 'npmregistry', 'nps', 'nr', 'ns', 'ns-', 'ns0', 'ns01', 'ns02', 'ns03',
'ns04', 'ns1', 'ns10', 'ns101', 'ns102', 'ns11', 'ns12', 'ns13', 'ns14', 'ns15',
'ns16', 'ns17', 'ns18', 'ns19', 'ns1a', 'ns2', 'ns20', 'ns21', 'ns22', 'ns23',
'ns24', 'ns25', 'ns26', 'ns27', 'ns28', 'ns29', 'ns2a', 'ns3', 'ns30', 'ns31',
'ns32', 'ns33', 'ns34', 'ns35', 'ns36', 'ns37', 'ns38', 'ns39', 'ns4', 'ns40',
'ns41', 'ns42', 'ns43', 'ns44', 'ns45', 'ns5', 'ns50', 'ns51', 'ns52', 'ns55',
'ns6', 'ns60', 'ns61', 'ns62', 'ns63', 'ns64', 'ns7', 'ns70', 'ns8', 'ns9',
'ns_', 'nsa', 'nsb', 'nsc', 'nsk', 'nswc', 'nt', 'nt4', 'nt40', 'ntmail', 'ntp',
'ntp1', 'ntp2', 'ntp3', 'ntpd', 'ntserver', 'nu', 'nuevo', 'nuevosoft', 'nuke',
'nukualofa', 'null', 'nurse', 'nursing', 'nv', 'nw', 'nx', 'ny', 'nyc', 'nycap',
'nyx', 'nz', 'o', 'o1', 'o1.email', 'o2', 'oa', 'oak', 'oakland', 'oas',
'oasis', 'obelix', 'oberon', 'objentis', 'obs', 'oc', 'oc.pool', 'ocean', 'ocn',
'ocs', 'octopus', 'ocw', 'odin', 'odn', 'odyssey', 'oem', 'ofertas', 'offer',
'offers', 'office', 'office2', 'offices', 'offline', 'ogloszenia', 'oh', 'ohio',
'oilfield', 'oilkjm', 'ok', 'okc', 'okcyok', 'oklahoma', 'oklahomacity', 'old',
'old2', 'oldmail', 'oldsite', 'oldweb', 'oldwebmail', 'oldwww', 'olga', 'olimp',
'olive', 'oliver', 'olivia', 'olympus', 'om', 'oma', 'omah', 'omaha', 'omega',
'omicron', 'omsk', 'oncall', 'oncall-01', 'oncall-02', 'oncall-03', 'oncall-1',
'oncall-2', 'oncall-3', 'oncall01', 'oncall02', 'oncall03', 'oncall1',
'oncall2', 'oncall3', 'one', 'onepiece', 'online', 'online4-cert', 'ontario',
'onyx', 'op', 'opac', 'opel', 'open', 'openbsc', 'openbsd', 'openbts',
'openerp', 'openfire', 'opengoo', 'opengroup', 'openid', 'openload', 'openproj',
'openqa', 'openserver', 'opensolaris', 'opensource', 'opensta', 'opensuse',
'openview', 'openvms', 'openvpn', 'openwebload', 'openx', 'opera', 'operations',
'ops', 'ops0', 'ops01', 'ops02', 'ops1', 'ops2', 'opsware', 'opt',
'optimaltest', 'optusnet', 'opus', 'opus-01', 'opus-02', 'opus-03', 'opus-1',
'opus-2', 'opus-3', 'opus01', 'opus02', 'opus03', 'opus1', 'opus2', 'opus3',
'or', 'ora', 'oracle', 'orange', 'orbit', 'orca', 'orcanos', 'orchid', 'orcl',
'order', 'orders', 'oregon', 'orel', 'org', 'origin', 'origin-images',
'origin-video', 'origin-www', 'origsoft', 'orion', 'orlando', 'os', 'os390',
'oscar', 'osiris', 'oslo', 'oss', 'osx', 'ota', 'other', 'otmgr', 'otrs',
'ottawa', 'ouagadougou', 'out', 'outbound', 'outdial', 'outgoing', 'outlet',
'outlook', 'outside', 'ov', 'ovpn', 'owa', 'owa01', 'owa02', 'owa1', 'owa2',
'owb', 'owl', 'owncloud', 'ows', 'ox', 'oxford', 'oxnard', 'oxygen', 'oz', 'p',
'p1', 'p2', 'p2p', 'p3', 'p4', 'p80.pool', 'pa', 'pablo', 'pac', 'pacific',
'packages', 'pacs', 'pad', 'page', 'pager', 'pager-01', 'pager-02', 'pager-03',
'pager-1', 'pager-2', 'pager-3', 'pager01', 'pager02', 'pager03', 'pager1',
'pager2', 'pager3', 'pagerduty', 'pagerduty-01', 'pagerduty-02', 'pagerduty-03',
'pagerduty-1', 'pagerduty-2', 'pagerduty-3', 'pagerduty01', 'pagerduty02',
'pagerduty03', 'pagerduty1', 'pagerduty2', 'pagerduty3', 'pagers', 'pagers-01',
'pagers-02', 'pagers-03', 'pagers-1', 'pagers-2', 'pagers-3', 'pagers01',
'pagers02', 'pagers03', 'pagers1', 'pagers2', 'pagers3', 'pages', 'paginas',
'pagos', 'pai', 'painel', 'painelstats', 'palikir', 'palm', 'pan', 'panama',
'panda', 'pandora', 'panel', 'panelstats', 'panelstatsmail', 'panorama',
'pantera', 'panther', 'papa', 'paper', 'paradise', 'paramaribo', 'parents',
'paris', 'park', 'parking', 'parners', 'partner', 'partnerapi', 'partners',
'parts', 'party', 'pas', 'pascal', 'pass', 'passmark', 'passport', 'password',
'patch', 'patches', 'patrick', 'paul', 'paula', 'pay', 'payment', 'payments',
'paynow', 'paypal', 'payroll', 'pb', 'pbx', 'pc', 'pc01', 'pc1', 'pc10',
'pc101', 'pc11', 'pc12', 'pc13', 'pc14', 'pc15', 'pc16', 'pc17', 'pc18', 'pc19',
'pc2', 'pc20', 'pc21', 'pc22', 'pc23', 'pc24', 'pc25', 'pc26', 'pc27', 'pc28',
'pc29', 'pc3', 'pc30', 'pc31', 'pc32', 'pc33', 'pc34', 'pc35', 'pc36', 'pc37',
'pc38', 'pc39', 'pc4', 'pc40', 'pc41', 'pc42', 'pc43', 'pc44', 'pc45', 'pc46',
'pc47', 'pc48', 'pc49', 'pc5', 'pc50', 'pc51', 'pc52', 'pc53', 'pc54', 'pc55',
'pc56', 'pc57', 'pc58', 'pc59', 'pc6', 'pc60', 'pc7', 'pc8', 'pc9',
'pcanywhere', 'pcbsd', 'pcgk', 'pcmail', 'pcs', 'pcstun', 'pcu', 'pd', 'pda',
'pdc', 'pdc1', 'pdf', 'pdns', 'pds', 'pe', 'peach', 'pearl', 'pec', 'pedro',
'peercast', 'pegasus', 'penadmin1', 'penarth.cit', 'pendrell', 'penguin',
'pennsylvania', 'penza', 'people', 'peoplesoft', 'pepper', 'perforce',
'performancetester', 'perl', 'perm', 'persephone', 'perseus', 'personal',
'peru', 'pet', 'peter', 'pets', 'pf', 'pfsense', 'pg', 'pg-01', 'pg-02',
'pg-03', 'pg-1', 'pg-2', 'pg-3', 'pg01', 'pg02', 'pg03', 'pg1', 'pg2', 'pg3',
'pgadmin', 'pgp', 'pgsql', 'ph', 'phabricator', 'phabricator-01',
'phabricator-02', 'phabricator-03', 'phabricator-1', 'phabricator-2',
'phabricator-3', 'phabricator01', 'phabricator02', 'phabricator03',
'phabricator1', 'phabricator2', 'phabricator3', 'phantom', 'pharmacy', 'phd',
'phi', 'phil', 'philadelphia', 'phnom', 'phnx', 'phobos', 'phoenix', 'phoeniz',
'phone', 'phones', 'photo', 'photogallery', 'photon', 'photos', 'php', 'php5',
'phpadmin', 'phpbb', 'phpgroupware', 'phplist', 'phpmyadmin', 'phprojekt',
'phpunit', 'phys', 'physics', 'pi', 'pic', 'picard', 'pico', 'pics', 'picture',
'pictures', 'pidlabelling.users', 'pilot', 'pim', 'ping', 'pink', 'pinky',
'pinnacle', 'pioneer', 'pipex-gw', 'pisces', 'pittsburgh', 'pitweb',
'pitweb-01', 'pitweb-02', 'pitweb-03', 'pitweb-1', 'pitweb-2', 'pitweb-3',
'pitweb01', 'pitweb02', 'pitweb03', 'pitweb1', 'pitweb2', 'pitweb3', 'pivotal',
'piwik', 'piwik-01', 'piwik-02', 'piwik-03', 'piwik-1', 'piwik-2', 'piwik-3',
'piwik01', 'piwik02', 'piwik03', 'piwik1', 'piwik2', 'piwik3', 'pix', 'pixel',
'pjsip', 'pk', 'pki', 'pl', 'plala', 'plan', 'planet', 'planisware', 'planning',
'plano', 'plant', 'plastic', 'platform', 'platform-eb', 'platinum', 'plato',
'platon', 'play', 'player', 'playground', 'plaza', 'plesk', 'pliki', 'pltn13',
'plus', 'pluslatex.users', 'pluto', 'pluton', 'pm', 'pm03-1', 'pm04-1', 'pm1',
'pma', 'pmo', 'pms', 'pn', 'pns', 'po', 'poczta', 'podcast', 'podgorica',
'point', 'poker', 'pol', 'polar', 'polaris', 'police', 'policy', 'polipo',
'polipo-01', 'polipo-02', 'polipo-03', 'polipo-1', 'polipo-2', 'polipo-3',
'polipo01', 'polipo02', 'polipo03', 'polipo1', 'polipo2', 'polipo3', 'poll',
'polladmin', 'polls', 'pollux', 'polycom', 'pool', 'pools', 'pop', 'pop2',
'pop3', 'popo', 'port', 'portail', 'portal', 'portal1', 'portal2', 'portals',
'portaltest', 'portfolio', 'portland', 'porto', 'pos', 'poseidon', 'post',
'posta', 'posta01', 'posta02', 'posta03', 'postales', 'postfix', 'postfixadmin',
'postgres', 'postgres-01', 'postgres-02', 'postgres-03', 'postgres-1',
'postgres-2', 'postgres-3', 'postgres01', 'postgres02', 'postgres03',
'postgres1', 'postgres2', 'postgres3', 'postgresd', 'postgresd-01',
'postgresd-02', 'postgresd-03', 'postgresd-1', 'postgresd-2', 'postgresd-3',
'postgresd01', 'postgresd02', 'postgresd03', 'postgresd1', 'postgresd2',
'postgresd3', 'postgresql', 'postman', 'postmaster', 'postoffice', 'power',
'power1', 'pp', 'ppc', 'ppp', 'ppp1', 'ppp10', 'ppp11', 'ppp12', 'ppp13',
'ppp14', 'ppp15', 'ppp16', 'ppp17', 'ppp18', 'ppp19', 'ppp2', 'ppp20', 'ppp21',
'ppp3', 'ppp4', 'ppp5', 'ppp6', 'ppp7', 'ppp8', 'ppp9', 'pppoe', 'pps', 'pps00',
'pptp', 'pr', 'praca', 'practitest', 'prague', 'praia', 'pre', 'pre-prod',
'premier', 'premium', 'prensa', 'preprod', 'present', 'president', 'press',
'presse', 'prestashop', 'prestige', 'pretoria', 'preview', 'price', 'pride',
'prima', 'primary', 'primavera', 'prime', 'prince', 'princess', 'principal',
'print', 'printer', 'printserv', 'printserver', 'pristina', 'priv', 'privacy',
'private', 'privoxy', 'privoxy-01', 'privoxy-02', 'privoxy-03', 'privoxy-1',
'privoxy-2', 'privoxy-3', 'privoxy01', 'privoxy02', 'privoxy03', 'privoxy1',
'privoxy2', 'privoxy3', 'pro', 'proba', 'problemtracker', 'prod',
'prod-empresarial', 'prod-infinitum', 'prodigy', 'product', 'production',
'products', 'prof', 'profile', 'profiles', 'program', 'progress', 'prohome',
'project', 'projecthq', 'projectpier', 'projectplace', 'projects',
'projectspaces', 'projektron', 'projistics', 'prometheus', 'prometheus-01',
'prometheus-02', 'prometheus-03', 'prometheus-1', 'prometheus-2',
'prometheus-3', 'prometheus01', 'prometheus02', 'prometheus03', 'prometheus1',
'prometheus2', 'prometheus3', 'promo', 'promotion', 'property', 'proteo',
'proteus', 'proto', 'proton', 'prototype', 'prova', 'proxy', 'proxy1', 'proxy2',
'proxy3', 'proyectos', 'prtg', 'prueba', 'pruebas', 'ps', 'psi', 'psnext',
'psp', 'pss', 'psy', 'psychologie', 'pt', 'ptld', 'ptr', 'pub', 'public',
'publicapi', 'publish', 'pubs', 'pulsar', 'puma', 'pumpkin', 'puppet',
'puppet-01', 'puppet-02', 'puppet-03', 'puppet-1', 'puppet-2', 'puppet-3',
'puppet01', 'puppet02', 'puppet03', 'puppet1', 'puppet2', 'puppet3',
'pureagent', 'pureload', 'puretest', 'purple', 'push', 'puzzle', 'pv', 'pw',
'pw.openvpn', 'py', 'pylot', 'pyongyang', 'python', 'q', 'qa', 'qa1',
'qadirector', 'qagatekeeper', 'qaliber', 'qaload', 'qamanager', 'qatraq',
'qavgatekeeper', 'qavmgk', 'qb', 'qh', 'qmail', 'qmetry', 'qmtest', 'qnx',
'qotd', 'qpack', 'qq', 'qr', 'qtest', 'qtronic', 'quake', 'qualify', 'quality',
'quangcao', 'quantum', 'quebec', 'queen', 'queens', 'query', 'quickbase',
'quicktest', 'quicktestpro', 'quicktime', 'quit', 'quito', 'quiz', 'quizadmin',
'quote', 'quotes', 'quotium', 'quran', 'qwqee', 'qwqwq', 'qwrer', 'r', 'r01',
'r02', 'r1', 'r2', 'r25', 'r2d2', 'r3', 'ra', 'rabat', 'rabbit', 'rabota',
'rachel', 'rack', 'rad', 'radar', 'radio', 'radio1', 'radius', 'radius.auth',
'radius1', 'radius2', 'rain', 'rainbow', 'ramstein', 'range217-42',
'range217-43', 'range217-44', 'range86-128', 'range86-129', 'range86-130',
'range86-131', 'range86-132', 'range86-133', 'range86-134', 'range86-135',
'range86-136', 'range86-137', 'range86-138', 'range86-139', 'range86-140',
'range86-141', 'range86-142', 'range86-143', 'range86-144', 'range86-145',
'range86-146', 'range86-147', 'range86-148', 'range86-149', 'range86-150',
'range86-151', 'range86-152', 'range86-153', 'range86-154', 'range86-155',
'range86-156', 'range86-157', 'range86-158', 'range86-159', 'range86-160',
'range86-161', 'range86-162', 'range86-163', 'range86-164', 'range86-165',
'range86-166', 'range86-167', 'range86-168', 'range86-169', 'range86-170',
'range86-171', 'range86-172', 'range86-173', 'range86-174', 'range86-176',
'range86-177', 'range86-178', 'range86-179', 'range86-180', 'range86-181',
'range86-182', 'range86-183', 'range86-184', 'range86-185', 'range86-186',
'range86-187', 'range86-188', 'range86-189', 'rangoon', 'rank', 'ranking',
'rap', 'rapid', 'rapidsite', 'raptor', 'ras', 'rating', 'raven', 'rb', 'rc',
'rcs', 'rcsntx', 'rd', 'rdns', 'rdns2', 'rdp', 'rds', 're', 'read', 'reader',
'real', 'realese', 'realestate', 'realmedia', 'realserver', 'realty',
'rebecca.users', 'rec', 'recherche', 'record', 'recovery', 'recruit',
'recruiting', 'recruitment', 'red', 'redhat', 'redir', 'redirect', 'redis',
'redis-01', 'redis-02', 'redis-03', 'redis-1', 'redis-2', 'redis-3', 'redis01',
'redis02', 'redis03', 'redis1', 'redis2', 'redis3', 'redmine', 'ref',
'reference', 'reg', 'register', 'registrar', 'registration', 'registro',
'registry', 'regs', 'reklam', 'reklama', 'relax', 'relay', 'relay-01',
'relay-02', 'relay-03', 'relay-1', 'relay-2', 'relay-3', 'relay01', 'relay02',
'relay03', 'relay1', 'relay2', 'relay3', 'relay4', 'release', 'rem', 'remedy',
'remote', 'remote2', 'remstats', 'remus', 'renew', 'renewal', 'rent', 'rental',
'rep', 'repair', 'repo', 'report', 'reporter', 'reporting', 'reports',
'repository', 'request', 'rerew', 'res', 'research', 'reseller', 'resellers',
'reservation', 'reservations', 'reserve', 'reserved', 'resnet', 'resource',
'resources', 'rest', 'restricted', 'result', 'results', 'resumenes', 'retail',
'rev', 'reverse', 'review', 'reviews', 'rex', 'reykjavik', 'rg', 'rh', 'rhea',
'rhel', 'rhino', 'rho', 'rhodeisland', 'ri', 'rich', 'richard', 'richmond',
'ricky', 'riga', 'rigel', 'ring', 'rio', 'ris', 'risc', 'river', 'riyadh', 'rm',
'rma', 'rmi', 'rmr1', 'rms', 'rnd', 'ro', 'roadmap', 'roadmap-01', 'roadmap-02',
'roadmap-03', 'roadmap-1', 'roadmap-2', 'roadmap-3', 'roadmap01', 'roadmap02',
'roadmap03', 'roadmap1', 'roadmap2', 'roadmap3', 'robert', 'robin', 'robinhood',
'robo', 'robot', 'rochester', 'rock', 'rocky', 'roger', 'rogue', 'roma',
'roman', 'romania', 'rome', 'romeo', 'romulus', 'root', 'rootservers', 'rosa',
'rose', 'roseau', 'rostov', 'roundcube', 'roundup', 'route', 'router',
'router1', 'router2', 'routernet', 'rp', 'rpc', 'rpg', 'rpm', 'rps', 'rr',
'rrhh', 'rs', 'rs1', 'rs2', 'rsa', 'rsc', 'rsm', 'rss', 'rsync', 'rsyslog',
'rsyslog-01', 'rsyslog-02', 'rsyslog-03', 'rsyslog-1', 'rsyslog-2', 'rsyslog-3',
'rsyslog01', 'rsyslog02', 'rsyslog03', 'rsyslog1', 'rsyslog2', 'rsyslog3', 'rt',
'rtc5', 'rtelnet', 'rth', 'rtr', 'rtr01', 'rtr1', 'ru', 'ruby', 'rugby', 'rune',
'rus', 'russia', 'russian', 'rw', 'rwhois', 'ryan', 'ryazan', 's', 's0', 's01',
's02', 's1', 's10', 's11', 's111', 's112', 's114', 's12', 's123', 's13', 's14',
's15', 's16', 's17', 's18', 's19', 's2', 's20', 's201', 's202', 's203', 's204',
's207', 's21', 's216', 's22', 's221', 's222', 's224', 's227', 's23', 's230',
's233', 's236', 's237', 's238', 's239', 's24', 's241', 's245', 's247', 's248',
's249', 's25', 's251', 's252', 's253', 's254', 's255', 's256', 's257', 's258',
's259', 's26', 's262', 's264', 's265', 's266', 's267', 's268', 's269', 's27',
's270', 's271', 's272', 's273', 's274', 's275', 's276', 's277', 's278', 's28',
's280', 's281', 's285', 's286', 's287', 's288', 's289', 's29', 's290', 's291',
's295', 's296', 's297', 's298', 's299', 's3', 's30', 's301', 's302', 's303',
's304', 's305', 's306', 's307', 's308', 's309', 's31', 's310', 's311', 's312',
's313', 's314', 's315', 's316', 's317', 's318', 's32', 's320', 's321', 's324',
's325', 's326', 's329', 's33', 's330', 's331', 's332', 's333', 's334', 's335',
's336', 's337', 's338', 's339', 's34', 's340', 's341', 's342', 's343', 's344',
's345', 's346', 's347', 's348', 's349', 's35', 's350', 's351', 's352', 's353',
's354', 's355', 's356', 's357', 's4', 's40', 's401', 's402', 's403', 's406',
's410', 's411', 's412', 's413', 's414', 's415', 's416', 's417', 's418', 's419',
's420', 's421', 's422', 's424', 's425', 's426', 's427', 's428', 's429', 's430',
's431', 's432', 's433', 's434', 's435', 's436', 's437', 's438', 's439', 's440',
's441', 's442', 's443', 's444', 's445', 's446', 's447', 's448', 's449', 's450',
's451', 's452', 's453', 's454', 's455', 's456', 's457', 's458', 's459', 's460',
's461', 's462', 's463', 's464', 's465', 's466', 's467', 's468', 's469', 's470',
's471', 's472', 's473', 's474', 's475', 's476', 's477', 's5', 's50', 's6', 's7',
's8', 's9', 'sa', 'saas', 'sabayon', 'sac', 'sacramento', 'sad', 'sadmin',
'safe', 'safety', 'saga', 'sage', 'sahi', 'sailing', 'saint', 'sakai', 'sakura',
'sale', 'sales', 'salome', 'salsa', 'saltlake', 'salud', 'sam', 'samara',
'samba', 'sametime', 'sami', 'samp', 'sample', 'samples', 'samsung', 'samurai',
'san', 'sanaa', 'sanantonio', 'sandbox', 'sandiego', 'sandy', 'sanfrancisco',
'sanjose', 'sante', 'santiago', 'santo', 'sao', 'sap', 'sapphire', 'saprouter',
'sar', 'sara', 'sarajevo', 'saratov', 'saruman', 'sas', 'sasa', 'saskatchewan',
'sasknet', 'sat', 'satellite', 'saturn', 'sauron', 'savannah', 'save',
'savecom', 'sb', 'sbc', 'sbs', 'sc', 'sca', 'scan', 'scanner', 'scarab', 'scc',
'sccs', 'schedule', 'schedules', 'school', 'schools', 'sci', 'science', 'scm',
'sco', 'scorpio', 'scorpion', 'scotland', 'scott', 'scotty', 'scp',
'screenshot', 'script', 'scripts', 'scrm01', 'sd', 'sdc', 'sdf', 'sdsl', 'se',
'se0', 'se1', 'sea', 'seam', 'seapine', 'search', 'search1', 'search2',
'season', 'seattle', 'sec', 'secim', 'secret', 'secure', 'secure.dev',
'secure1', 'secure2', 'secure3', 'secure4', 'secured', 'securedrop',
'securedrop-01', 'securedrop-02', 'securedrop-03', 'securedrop-1',
'securedrop-2', 'securedrop-3', 'securedrop01', 'securedrop02', 'securedrop03',
'securedrop1', 'securedrop2', 'securedrop3', 'securemail', 'securid',
'security', 'seed', 'seg', 'segment-119-226', 'segment-119-227',
'segment-124-30', 'segment-124-7', 'seguro', 'selene', 'selenium', 'self',
'selfservice', 'sem', 'seminar', 'send', 'sender', 'sendmail', 'sensu',
'sentinel', 'sentry', 'seo', 'seoul', 'serenity', 'seri', 'serial', 'serv',
'serv1', 'serv2', 'server', 'server01', 'server02', 'server1', 'server10',
'server11', 'server12', 'server13', 'server14', 'server15', 'server18',
'server19', 'server2', 'server20', 'server22', 'server3', 'server4', 'server5',
'server6', 'server7', 'server8', 'server9', 'servers', 'service', 'servicedesk',
'services', 'services2', 'servicio', 'servicios', 'servicos', 'servidor',
'servlet', 'seth', 'setup', 'seven', 'severa', 'sex', 'sexy', 'sf', 'sfa',
'sfldmi', 'sftp', 'sg', 'sgs', 'sgsn', 'sh', 'sh1', 'sh2', 'shadow', 'shanghai',
'share', 'shared', 'sharepoint', 'shares', 'shareware', 'shark', 'sharpforge',
'shell', 'sherlock', 'shine', 'shipping', 'shiva', 'shms1', 'shms2', 'shop',
'shop1', 'shop2', 'shoppers', 'shopping', 'shorturl', 'shoutcast', 'show',
'showcase', 'shrek', 'shv', 'si', 'sia', 'sic', 'sie', 'siebel', 'siemens',
'sierra', 'sierracharlie.users', 'sig', 'siga', 'sigma', 'sign', 'signin',
'signup', 'silk', 'silkcentral', 'silkperformer', 'silver', 'sim', 'simon',
'simple', 'simpletest', 'simpletestmanagement', 'simpleticket', 'simulator',
'sina', 'singapore', 'sip', 'sip1', 'sip2', 'sipexternal', 'sipp', 'sipr',
'sirius', 'sis', 'sistema', 'sistemas', 'sit', 'site', 'site1', 'site2',
'sitebuilder', 'sitedefender', 'sitemap', 'sites', 'sitestream', 'siw', 'sj',
'sjc', 'sk', 'ski', 'skin', 'sklep', 'skopje', 'sky', 'skyline', 'skynet',
'skywalker', 'sl', 'sl-app1', 'sl-mon1', 'sl-mysql-db1', 'sl-od',
'sl-public-web1', 'sl-ts', 'sl-web1', 'sl-web2', 'sl-web3', 'slack',
'slackware', 'slave', 'slim', 'slkc', 'slmail', 'slsg', 'sm', 'smail', 'smart',
'smartesoft', 'smartload', 'smartphone', 'smartqm', 'smartscript', 'smartsheet',
'smc', 'smdb', 'sme', 'smg', 'smile', 'smith', 'smoke', 'smokeping', 'smp',
'smpp', 'sms', 'sms2', 'smsc', 'smt', 'smtp', 'smtp-out', 'smtp-out-01',
'smtp-relay', 'smtp0', 'smtp01', 'smtp02', 'smtp03', 'smtp1', 'smtp10', 'smtp2',
'smtp3', 'smtp4', 'smtp5', 'smtp6', 'smtp7', 'smtpgw', 'smtphost', 'smtpout',
'smtprelayout', 'smtps', 'sn', 'snake', 'snantx', 'sndg02', 'sndgca', 'snfc21',
'sniffer', 'snmp', 'snmpd', 'snoopy', 'snorby', 'snorby-01', 'snorby-02',
'snorby-03', 'snorby-1', 'snorby-2', 'snorby-3', 'snorby01', 'snorby02',
'snorby03', 'snorby1', 'snorby2', 'snorby3', 'snort', 'snort-01', 'snort-02',
'snort-03', 'snort-1', 'snort-2', 'snort-3', 'snort01', 'snort02', 'snort03',
'snort1', 'snort2', 'snort3', 'snow', 'sns', 'sntcca', 'so', 'so-net', 'soa',
'soap', 'soapui', 'soc', 'socal', 'soccer', 'sochi', 'social', 'sof', 'sofia',
'soft', 'software', 'softwareresearch', 'sol', 'solar', 'solaris', 'soleil',
'solo', 'solr', 'solutions', 'song', 'sonia', 'sonic', 'sonicwall', 'sony',
'sophia', 'sophos', 'soporte', 'sora', 'sorry', 'sos', 'soul', 'sound',
'source', 'sourcecode', 'sourcesafe', 'south', 'southcarolina', 'southdakota',
'southeast', 'southwest', 'sp', 'sp1', 'sp2', 'spa', 'space', 'spain', 'spam',
'spam1', 'spamfilter', 'spanish', 'spare', 'spark', 'spawar', 'spb', 'specflow',
'special', 'specials', 'spectre', 'spectrum', 'speed', 'speedtest',
'speedtest1', 'speedtest2', 'speedy', 'spf', 'sphinx', 'spiceworks', 'spider',
'spiderduck01', 'spiderduck1', 'spiderman', 'spiratest', 'spirit', 'spkn',
'splash', 'splunk', 'spock', 'spokane', 'spokes', 'spoon', 'spor', 'sport',
'sports', 'spot', 'spotlight', 'spp', 'spring', 'springfield', 'sprint',
'spruce', 'spruce-goose-bg', 'sps', 'sq', 'sq1', 'sqa', 'sql', 'sql0', 'sql01',
'sql1', 'sql2', 'sql3', 'sql7', 'sqladmin', 'sqlserver', 'squid', 'squid-01',
'squid-02', 'squid-03', 'squid-1', 'squid-2', 'squid-3', 'squid01', 'squid02',
'squid03', 'squid1', 'squid2', 'squid3', 'squirrel', 'squirrel-01',
'squirrel-02', 'squirrel-03', 'squirrel-1', 'squirrel-2', 'squirrel-3',
'squirrel01', 'squirrel02', 'squirrel03', 'squirrel1', 'squirrel2', 'squirrel3',
'squirrelmail', 'squirrelmail-01', 'squirrelmail-02', 'squirrelmail-03',
'squirrelmail-1', 'squirrelmail-2', 'squirrelmail-3', 'squirrelmail01',
'squirrelmail02', 'squirrelmail03', 'squirrelmail1', 'squirrelmail2',
'squirrelmail3', 'squish', 'sr', 'sr2', 'src', 'srs', 'srv', 'srv01', 'srv1',
'srv2', 'srv3', 'srv4', 'srv5', 'srv6', 'ss', 'ss1', 'ss7', 'ssc', 'ssd', 'ssh',
'ssl', 'ssl0', 'ssl01', 'ssl1', 'ssl2', 'ssltest', 'sslvpn', 'sso', 'ssp',
'sss', 'st', 'st1', 'st2', 'st3', 'sta', 'staff', 'stage', 'stage1', 'stage2',
'stager', 'stager-01', 'stager-02', 'stager-03', 'stager-1', 'stager-2',
'stager-3', 'stager01', 'stager02', 'stager03', 'stager1', 'stager2', 'stager3',
'stagging', 'staging', 'staging2', 'stalker', 'standby', 'star', 'stargate',
'stars', 'start', 'starwars', 'stat', 'stat1', 'static', 'static-site',
'static.origin', 'static1', 'static2', 'static3', 'static4', 'staticip',
'statics', 'station', 'statistics', 'statistik', 'stats', 'stats2', 'status',
'stavropol', 'stc', 'std', 'steam', 'stella', 'step', 'steve', 'steven', 'stg',
'stl2mo', 'stlouis', 'stlsmo', 'stock', 'stockholm', 'stocks', 'stone',
'storage', 'storage1', 'storage2', 'store', 'store1', 'storefront', 'stores',
'storm', 'story', 'storytestiq', 'stp', 'stream', 'stream.origin', 'stream1',
'stream2', 'stream3', 'streamer', 'streaming', 'stronghold', 'strongmail',
'sts', 'stu', 'stub', 'stud', 'student', 'student1', 'student2', 'students',
'studio', 'study', 'stuff', 'stun', 'style', 'styx', 'su', 'sub', 'submit',
'subs', 'subscribe', 'subset.pool', 'subversion', 'sugar', 'sugarcrm', 'summer',
'sun', 'sun0', 'sun01', 'sun02', 'sun1', 'sun2', 'sunny', 'sunrise', 'sunset',
'sunshine', 'super', 'superman', 'suporte', 'supplier', 'suppliers', 'support',
'support1', 'support2', 'supportworks', 'surf', 'suricata', 'suricata-01',
'suricata-02', 'suricata-03', 'suricata-1', 'suricata-2', 'suricata-3',
'suricata01', 'suricata02', 'suricata03', 'suricata1', 'suricata2', 'suricata3',
'survey', 'surveys', 'sus', 'suse', 'suva', 'suzuki', 'sv', 'sv1', 'sv2', 'sv3',
'sv4', 'sv5', 'sv6', 'svc', 'svk', 'svn', 'svpn', 'sw', 'sw0', 'sw01', 'sw1',
'swan', 'sweden', 'swf', 'swift', 'switch', 'switch1', 'switzerland', 'sx',
'sy', 'sybase', 'sydney', 'sympa', 'sync', 'syndication', 'synergy', 'sys',
'sysadmin', 'sysback', 'syslog', 'syslog-01', 'syslog-02', 'syslog-03',
'syslog-1', 'syslog-2', 'syslog-3', 'syslog01', 'syslog02', 'syslog03',
'syslog1', 'syslog2', 'syslog3', 'syslogs', 'system', 'systems', 'sz', 't',
't-com', 't1', 't2', 't4', 'ta', 'tac', 'tacacs', 'tacas', 'tachikawa',
'tacoma', 'tag', 'tags', 'taipei', 'taiwan', 'talent', 'talk', 'tallinn',
'tampa', 'tango', 'tank', 'tap', 'tarawa', 'tarbaby', 'tardis', 'target',
'tashkent', 'task', 'tasks', 'tau', 'taurus', 'tb', 'tbcn', 'tbilisi', 'tc',
'tcl', 'tcm', 'tcs', 'tcso', 'td', 'tdatabrasil', 'te', 'tea', 'teacher',
'team', 'teamcenter', 'teamspeak', 'teamware', 'teamwork', 'teamworkpm', 'tec',
'tech', 'tech1', 'techexcel', 'techno', 'technology', 'techsupport',
'tegucigalpa', 'tehran', 'tel', 'tele', 'telecom', 'telefonia', 'telemar',
'telephone', 'telephony', 'telerik', 'telesp', 'telkomadsl', 'telnet', 'temp',
'tempest', 'template', 'templates', 'tempo', 'ten', 'tender', 'tenders',
'tennessee', 'tennis', 'tenrox', 'terminal', 'terminalserver', 'termserv',
'terra', 'tes', 'tesla', 'test', 'test-www', 'test.www', 'test01', 'test02',
'test03', 'test1', 'test10', 'test11', 'test12', 'test123', 'test13', 'test15',
'test2', 'test2.users', 'test22', 'test2k', 'test3', 'test4', 'test5', 'test6',
'test7', 'test8', 'test9', 'testajax', 'testasp', 'testaspnet', 'testbed',
'testbench', 'testbl', 'testblog', 'testbrvps', 'testcase', 'testcf',
'testcomplete', 'testdirector', 'testdrive', 'teste', 'tester', 'testes',
'testforum', 'testing', 'testitools', 'testjsp', 'testlab', 'testlink',
'testlinux', 'testlog', 'testmail', 'testman', 'testmanager', 'testmaster',
'testmasters', 'testo', 'testopia', 'testoptimal', 'testpartner', 'testphp',
'testportal', 'testrail', 'testrun', 'tests', 'testserver', 'testshop',
'testsite', 'testsql', 'testsuite', 'testtest', 'testtrack', 'testuff',
'testup', 'testvb', 'testweb', 'testworks', 'testwww', 'testxp', 'testy',
'teszt', 'texas', 'text', 'texttest', 'tf', 'tfn', 'tfs', 'tftp', 'tg', 'tgp',
'tgrrre', 'tgtggb', 'th', 'thailand', 'thankyou', 'thebest', 'theme', 'themes',
'theta', 'thimphu', 'think', 'thomas', 'thor', 'thumb', 'thumbs', 'thunder',
'ti', 'tic', 'ticket', 'ticketing', 'tickets', 'tienda', 'tiger', 'tigris',
'tim', 'time', 'tina', 'tinp', 'tinyproxy', 'tinyproxy-01', 'tinyproxy-02',
'tinyproxy-03', 'tinyproxy-1', 'tinyproxy-2', 'tinyproxy-3', 'tinyproxy01',
'tinyproxy02', 'tinyproxy03', 'tinyproxy1', 'tinyproxy2', 'tinyproxy3', 'tips',
'tirana', 'titan', 'tivoli', 'tj', 'tk', 'tld', 'tm', 'tmp', 'tms', 'tn', 'to',
'todo', 'toko', 'tokyo', 'toledo', 'tom', 'tomcat', 'tommy', 'tomsk', 'ton',
'tool', 'toolbar', 'toolbox', 'tools', 'top', 'topaz', 'toplayer', 'tor',
'tor-01', 'tor-02', 'tor-03', 'tor-1', 'tor-2', 'tor-3', 'tor01', 'tor02',
'tor03', 'tor1', 'tor2', 'tor3', 'tornado', 'toronto', 'torpedo', 'torrelay',
'torrelay-01', 'torrelay-02', 'torrelay-03', 'torrelay-1', 'torrelay-2',
'torrelay-3', 'torrelay01', 'torrelay02', 'torrelay03', 'torrelay1',
'torrelay2', 'torrelay3', 'torrent', 'total', 'toto', 'touch', 'tour',
'tourism', 'tours', 'tower', 'tower-01', 'tower-02', 'tower-03', 'tower-1',
'tower-2', 'tower-3', 'tower01', 'tower02', 'tower03', 'tower1', 'tower2',
'tower3', 'toyota', 'tp', 'tpgi', 'tplan', 'tpmsqr01', 'tps', 'tr', 'trac',
'track', 'tracker', 'trackersuite', 'tracking', 'trade', 'traffic', 'train',
'training', 'trans', 'transfer', 'transfers', 'transit', 'translate',
'transport', 'travel', 'travel2', 'traveler', 'travian', 'trial', 'tricentis',
'trident', 'trinidad', 'trinity', 'trio', 'tripoli', 'tristan', 'triton', 'trk',
'troy', 'trunk', 'try', 'ts', 'ts1', 'ts2', 'ts3', 'ts31', 'tsg', 'tsinghua',
'tss', 'tst', 'tsweb', 'tt', 'tts', 'ttt', 'ttyulecheng', 'tuan', 'tube',
'tucson', 'tukrga', 'tukw', 'tula', 'tulip', 'tulsa', 'tumb', 'tumblr', 'tunis',
'tunnel', 'turbo', 'turing', 'turismo', 'turkey', 'tutor', 'tutorials', 'tux',
'tv', 'tv2', 'tvadmin', 'tver', 'tw', 'twcny', 'twiki', 'twist', 'twitter',
'two', 'twr1', 'tx', 'txr', 'ty', 'typo3', 'tyumen', 'tz', 'u', 'ua', 'uat',
'ubidesk', 'ubuntu', 'uc', 'ucom', 'uddi', 'uesgh2x', 'ufa', 'ug', 'ui', 'uio',
'uk', 'ukgroup', 'ukr', 'ul', 'ulaanbaatar', 'ultra', 'ulyanovsk', 'um', 'uma',
'ums', 'un', 'unassigned', 'unawave', 'undefined', 'undefinedhost', 'uni',
'unicorn', 'uniform', 'uninet', 'union', 'unitedkingdom', 'unitedstates',
'unity', 'universal', 'universe', 'unix', 'unixware', 'unk', 'unknown',
'unreal', 'unspec170108', 'unspec207128', 'unspec207129', 'unspec207130',
'unspec207131', 'unsubscribe', 'unused', 'unused-space', 'uol', 'up', 'upc',
'upc-a', 'upc-h', 'upc-i', 'upc-j', 'update', 'update2', 'updates', 'upgrade',
'upl', 'upload', 'upload2', 'uploads', 'ups', 'ups1', 'upsilon', 'uptime',
'ural', 'uranus', 'urban', 'urchin', 'url', 'us', 'us.m', 'us1', 'us2', 'usa',
'usbank', 'usenet', 'user', 'users', 'userstream', 'ut', 'utah', 'utest',
'util', 'utilities', 'utility', 'utm', 'uunet', 'uxr3', 'uxr4', 'uxs1r',
'uxs2r', 'uy', 'uz', 'v', 'v1', 'v2', 'v28', 'v3', 'v4', 'v5', 'v6', 'va',
'vader', 'vaduz', 'vaiaku', 'valentine', 'validclick', 'validip', 'valletta',
'van', 'vancouver', 'vanilla', 'vantive', 'varnish', 'varnish-01', 'varnish-02',
'varnish-03', 'varnish-1', 'varnish-2', 'varnish-3', 'varnish01', 'varnish02',
'varnish03', 'varnish1', 'varnish2', 'varnish3', 'vas', 'vatican', 'vault',
'vb', 'vc', 'vc1', 'vcenter', 'vcs', 'vcse', 'vd', 'vdi', 'vds', 've',
'vebstage3', 'vector', 'vega', 'vegas', 'vela', 'veloxzone', 'vend', 'vendor',
'vendors', 'venus', 'vera', 'verify', 'verisium', 'veritas', 'vermont',
'veronica', 'vesta', 'vg', 'vhost', 'vi', 'victor', 'victoria', 'victory',
'vid1', 'vid2', 'video', 'video1', 'video2', 'video3', 'videoconf', 'videos',
'vie', 'vienna', 'vientiane', 'vietnam', 'view', 'viking', 'vilnius', 'vintage',
'violet', 'vip', 'vip1', 'vip2', 'viper', 'virginia', 'virgo', 'virtual',
'virtual2', 'virus', 'visa', 'visio', 'vision', 'vista', 'vita', 'viva',
'vivaldi', 'vk', 'vl', 'vlad', 'vladimir', 'vladivostok', 'vlan0', 'vlan1',
'vm', 'vm0', 'vm1', 'vm2', 'vm3', 'vm4', 'vmail', 'vms', 'vmserver', 'vmware',
'vn', 'vnc', 'vncrobot', 'vo', 'vod', 'vodacom', 'voice', 'voicemail', 'void',
'voip', 'volga', 'volgograd', 'vologda', 'voodoodigital.users', 'voronezh',
'vote', 'voyage', 'voyager', 'vp', 'vperformer', 'vpgk', 'vpmi', 'vpn', 'vpn0',
'vpn01', 'vpn02', 'vpn1', 'vpn2', 'vpn3', 'vpproxy', 'vps', 'vps1', 'vps2',
'vps3', 'vps4', 'vpstun', 'vr', 'vs', 'vs1', 'vsnl', 'vsp', 'vstagingnew', 'vt',
'vtest', 'vu', 'vulcan', 'vvv', 'vz', 'w', 'w0', 'w1', 'w10', 'w11', 'w12',
'w13', 'w14', 'w15', 'w17', 'w18', 'w19', 'w2', 'w20', 'w21', 'w22', 'w23',
'w24', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9', 'wa', 'wagner', 'wais',
'wakwak', 'walker', 'wall', 'wallace', 'wallet', 'wallpapers', 'walter', 'wam',
'wan', 'wap', 'wap1', 'wap2', 'wap3', 'war', 'warehouse', 'warez', 'warsaw',
'washington', 'watch', 'watchdog', 'water', 'watin', 'watir', 'watson', 'wave',
'wb', 'wc', 'wc3', 'wcm', 'wcs', 'wd', 'we', 'weather', 'web', 'web01', 'web02',
'web03', 'web04', 'web05', 'web06', 'web07', 'web08', 'web1', 'web10', 'web11',
'web12', 'web13', 'web14', 'web15', 'web16', 'web17', 'web18', 'web19', 'web2',
'web20', 'web21', 'web22', 'web23', 'web24', 'web26', 'web2project', 'web2test',
'web3', 'web4', 'web5', 'web6', 'web7', 'web8', 'web9', 'webaccess', 'webadmin',
'webaii', 'webalizer', 'webapp', 'webapps', 'webboard', 'webcache', 'webcam',
'webcast', 'webchat', 'webcon', 'webconf', 'webct', 'webdata', 'webdav',
'webdesign', 'webdev', 'webdisk', 'webdisk.admin', 'webdisk.ads',
'webdisk.beta', 'webdisk.billing', 'webdisk.blog', 'webdisk.cdn',
'webdisk.chat', 'webdisk.client', 'webdisk.crm', 'webdisk.demo', 'webdisk.dev',
'webdisk.directory', 'webdisk.download', 'webdisk.email', 'webdisk.en',
'webdisk.es', 'webdisk.facebook', 'webdisk.files', 'webdisk.forum',
'webdisk.forums', 'webdisk.gallery', 'webdisk.games', 'webdisk.help',
'webdisk.images', 'webdisk.img', 'webdisk.info', 'webdisk.jobs', 'webdisk.m',
'webdisk.mail', 'webdisk.media', 'webdisk.members', 'webdisk.mobile',
'webdisk.new', 'webdisk.news', 'webdisk.old', 'webdisk.portal',
'webdisk.projects', 'webdisk.radio', 'webdisk.sandbox', 'webdisk.search',
'webdisk.secure', 'webdisk.shop', 'webdisk.sms', 'webdisk.staging',
'webdisk.static', 'webdisk.store', 'webdisk.support', 'webdisk.test',
'webdisk.travel', 'webdisk.video', 'webdisk.videos', 'webdisk.webmail',
'webdisk.wiki', 'webdisk.wordpress', 'webdisk.wp', 'webdns1', 'webdns2',
'webdocs', 'webdriver', 'webfarm', 'webftp', 'webhelp', 'webhost', 'webhosting',
'webinar', 'webinars', 'webking', 'weblib', 'webload', 'weblog', 'weblogic',
'webmail', 'webmail.control', 'webmail.controlpanel', 'webmail.cp',
'webmail.cpanel', 'webmail.hosting', 'webmail1', 'webmail2', 'webmail3',
'webmaster', 'webmin', 'webportal', 'webproxy', 'webring', 'webs', 'webserv',
'webserver', 'webservice', 'webservices', 'webshop', 'website', 'websites',
'webspace', 'websphere', 'webspoc', 'websrv', 'websrvr', 'webstats', 'webster',
'webstore', 'websvr', 'webtest', 'webtools', 'webtrends', 'webtv', 'webvpn',
'wedding', 'welcome', 'wellington', 'wellness', 'wep', 'wep1', 'west',
'westnet', 'westvirginia', 'wf', 'wg', 'whatsup', 'whiskey', 'white', 'whm',
'whmcs', 'whois', 'wholesale', 'wi', 'wichita', 'widget', 'widgets', 'wifi',
'wiki', 'wililiam', 'will', 'willow', 'wilson', 'wimax-client', 'win', 'win01',
'win02', 'win1', 'win10', 'win11', 'win12', 'win2', 'win2000', 'win2003',
'win2k', 'win2k3', 'win3', 'win4', 'win5', 'win7', 'win8', 'wind', 'windhoek',
'windmill', 'windows', 'windows01', 'windows02', 'windows1', 'windows2',
'windows2000', 'windows2003', 'windowsxp', 'windu', 'wine', 'wing', 'wingate',
'wings', 'winner', 'winnt', 'winproxy', 'winrunner', 'wins', 'winserve',
'winter', 'winxp', 'wire', 'wireless', 'wisconsin', 'wise', 'wit', 'wizard',
'wksta1', 'wl', 'wlan', 'wlfrct', 'wm', 'wmail', 'wms', 'woh', 'wolf',
'wolverine', 'woman', 'women', 'wood', 'woody', 'word', 'wordpress',
'wordpress-01', 'wordpress-02', 'wordpress-03', 'wordpress-1', 'wordpress-2',
'wordpress-3', 'wordpress01', 'wordpress02', 'wordpress03', 'wordpress1',
'wordpress2', 'wordpress3', 'work', 'workbook', 'workengine', 'workflow',
'worklenz', 'works', 'workshop', 'workspace', 'workstation', 'world', 'worlds',
'wotnoh', 'wow', 'wowza', 'wp', 'wpad', 'wptest', 'wqwqw', 'wrike', 'write',
'ws', 'ws1', 'ws10', 'ws11', 'ws12', 'ws13', 'ws2', 'ws3', 'ws4', 'ws5', 'ws6',
'ws7', 'ws8', 'ws9', 'wss', 'wsus', 'wt', 'wusage', 'wv', 'ww', 'ww1', 'ww2',
'ww3', 'ww4', 'ww42', 'ww5', 'ww6', 'www', 'www-', 'www-01', 'www-02', 'www-1',
'www-2', 'www-a', 'www-b', 'www-backup', 'www-dev', 'www-int', 'www-new',
'www-old', 'www-test', 'www.1', 'www.123', 'www.2', 'www.a', 'www.abc',
'www.acc', 'www.ad', 'www.adimg', 'www.admin', 'www.adrian.users', 'www.ads',
'www.adserver', 'www.affiliates', 'www.alex', 'www.alex.users', 'www.alumni',
'www.analytics', 'www.android', 'www.api', 'www.app', 'www.apps', 'www.ar',
'www.archive', 'www.art', 'www.articles', 'www.ask', 'www.au', 'www.auto',
'www.b2b', 'www.bb', 'www.bbs', 'www.beta', 'www.betterday.users',
'www.billing', 'www.biz', 'www.blog', 'www.blogs', 'www.board', 'www.book',
'www.books', 'www.br', 'www.bugs', 'www.business', 'www.c', 'www.ca',
'www.careers', 'www.cat', 'www.catalog', 'www.cc', 'www.cd', 'www.cdn',
'www.charge', 'www.chat', 'www.chem', 'www.china', 'www.classifieds',
'www.client', 'www.clients', 'www.clifford.users', 'www.cloud', 'www.club',
'www.cms', 'www.cn', 'www.co', 'www.community', 'www.contact', 'www.cp',
'www.cpanel', 'www.crm', 'www.cs', 'www.d', 'www.data', 'www.dating',
'www.dav75.users', 'www.db', 'www.de', 'www.demo', 'www.demo2', 'www.demos',
'www.demwunz.users', 'www.design', 'www.dev', 'www.dev2', 'www.development',
'www.dir', 'www.director', 'www.directory', 'www.dl', 'www.docs', 'www.dom',
'www.domain', 'www.domains', 'www.download', 'www.downloads', 'www.drupal',
'www.dubious.users', 'www.edu', 'www.education', 'www.elearning', 'www.email',
'www.en', 'www.eng', 'www.english', 'www.es', 'www.eu', 'www.events',
'www.extranet', 'www.facebook', 'www.faq', 'www.fashion', 'www.fb',
'www.feedback', 'www.files', 'www.film', 'www.filme', 'www.flash', 'www.food',
'www.forms', 'www.forum', 'www.forums', 'www.foto', 'www.fr', 'www.free',
'www.ftp', 'www.fun', 'www.g', 'www.galeria', 'www.galleries', 'www.gallery',
'www.game', 'www.games', 'www.geo', 'www.german', 'www.gis', 'www.gmail',
'www.go', 'www.gobbit.users', 'www.gold', 'www.green', 'www.gsgou.users',
'www.health', 'www.help', 'www.helpdesk', 'www.hfccourse.users', 'www.hk',
'www.home', 'www.host', 'www.hosting', 'www.hotel', 'www.hotels', 'www.hr',
'www.hrm', 'www.i', 'www.id', 'www.image', 'www.images', 'www.img', 'www.in',
'www.india', 'www.info', 'www.intranet', 'www.ip', 'www.iphone', 'www.it',
'www.job', 'www.jobs', 'www.jocuri', 'www.joomla', 'www.journal', 'www.jp',
'www.katalog', 'www.kazan', 'www.kino', 'www.konkurs', 'www.lab', 'www.labs',
'www.law', 'www.learn', 'www.lib', 'www.library', 'www.life', 'www.link',
'www.links', 'www.live', 'www.login', 'www.loja', 'www.love', 'www.m',
'www.magento', 'www.mail', 'www.map', 'www.maps', 'www.market', 'www.marketing',
'www.math', 'www.mba', 'www.med', 'www.media', 'www.member', 'www.members',
'www.mm', 'www.mobi', 'www.mobil', 'www.mobile', 'www.money', 'www.monitor',
'www.moodle', 'www.movie', 'www.movies', 'www.movil', 'www.mp3', 'www.ms',
'www.msk', 'www.music', 'www.mx', 'www.my', 'www.new', 'www.news',
'www.newsite', 'www.newsletter', 'www.nl', 'www.noc', 'www.ns1', 'www.ns2',
'www.nsk', 'www.office', 'www.ogloszenia', 'www.old', 'www.online', 'www.p',
'www.panel', 'www.partner', 'www.partners', 'www.pay', 'www.pda', 'www.pe',
'www.photo', 'www.photos', 'www.php', 'www.pics', 'www.pidlabelling.users',
'www.pl', 'www.play', 'www.plb1', 'www.plb2', 'www.plb3', 'www.plb4',
'www.plb5', 'www.plb6', 'www.plus', 'www.pluslatex.users', 'www.poczta',
'www.portal', 'www.portfolio', 'www.pp', 'www.pr', 'www.press', 'www.preview',
'www.pro', 'www.project', 'www.projects', 'www.promo', 'www.proxy',
'www.prueba', 'www.pt', 'www.qa', 'www.radio', 'www.rebecca.users', 'www.reg',
'www.reklama', 'www.research', 'www.reseller', 'www.rss', 'www.ru', 'www.s',
'www.s1', 'www.sa', 'www.sales', 'www.samara', 'www.sandbox', 'www.saratov',
'www.sc', 'www.school', 'www.se', 'www.search', 'www.secure', 'www.seo',
'www.server', 'www.service', 'www.services', 'www.sg', 'www.shop',
'www.shopping', 'www.sierracharlie.users', 'www.site', 'www.sklep', 'www.slb1',
'www.slb2', 'www.slb3', 'www.slb4', 'www.slb5', 'www.slb6', 'www.sms',
'www.social', 'www.soft', 'www.software', 'www.soporte', 'www.spb',
'www.speedtest', 'www.sport', 'www.sports', 'www.ssl', 'www.staff', 'www.stage',
'www.staging', 'www.start', 'www.stat', 'www.static', 'www.stats', 'www.status',
'www.store', 'www.stream', 'www.student', 'www.subscribe', 'www.support',
'www.survey', 'www.svn', 'www.t', 'www.team', 'www.tech', 'www.temp',
'www.test', 'www.test1', 'www.test2', 'www.test2.users', 'www.test3',
'www.testing', 'www.themes', 'www.ticket', 'www.tickets', 'www.tienda',
'www.tools', 'www.top', 'www.tour', 'www.tr', 'www.training', 'www.travel',
'www.ts', 'www.tv', 'www.tw', 'www.twitter', 'www.ua', 'www.ufa', 'www.uk',
'www.up', 'www.update', 'www.upload', 'www.us', 'www.usa', 'www.v2', 'www.v28',
'www.v3', 'www.vb', 'www.vestibular', 'www.video', 'www.videos', 'www.vip',
'www.voodoodigital.users', 'www.wap', 'www.web', 'www.webdesign', 'www.webmail',
'www.webmaster', 'www.whois', 'www.wholesale', 'www.wiki', 'www.windows',
'www.wordpress', 'www.work', 'www.world', 'www.wp', 'www.www', 'www.www2',
'www.x', 'www.xml', 'www.xxx', 'www.youtube', 'www0', 'www01', 'www02', 'www1',
'www1-backup', 'www10', 'www11', 'www12', 'www13', 'www14', 'www15', 'www16',
'www17', 'www18', 'www19', 'www2', 'www2-backup', 'www20', 'www21', 'www22',
'www23', 'www24', 'www25', 'www26', 'www270', 'www3', 'www3-backup', 'www30',
'www31', 'www32', 'www36', 'www37', 'www39', 'www4', 'www41', 'www43', 'www44',
'www47', 'www48', 'www49', 'www5', 'www51', 'www54', 'www55', 'www56', 'www6',
'www61', 'www63', 'www64', 'www65', 'www66', 'www67', 'www68', 'www69', 'www7',
'www70', 'www74', 'www8', 'www81', 'www82', 'www9', 'www90', 'www_', 'wwwcache',
'wwwchat', 'wwwdev', 'wwwhost-ox001', 'wwwhost-port001', 'wwwhost-roe001',
'wwwmail', 'wwwnew', 'wwwold', 'wwws', 'wwwtest', 'wwww', 'wwwww', 'wwwx',
'wxsxc', 'wy', 'wyoming', 'x', 'x-ray', 'x1', 'x2', 'x25', 'x25gw', 'x25pad',
'x3', 'xanthus', 'xb', 'xcb', 'xdsl', 'xen', 'xen1', 'xen2', 'xena', 'xenapp',
'xenon', 'xeon', 'xg', 'xhtml', 'xhtmlunit', 'xi', 'xj', 'xlogan', 'xmail',
'xmas', 'xml', 'xml-simulator', 'xmpp', 'xot', 'xp', 'xplanner', 'xqual', 'xr',
'xray', 'xsc', 'xstudio', 'xtreme', 'xx', 'xxgk', 'xxx', 'xy', 'xyh', 'xyz',
'xz', 'y', 'y12', 'ya', 'yahoo', 'yamato', 'yamoussoukro', 'yankee', 'yaounde',
'yaroslavl', 'yb', 'ye', 'yellow', 'yeni', 'yerevan', 'yes', 'yjs', 'yn',
'yoda', 'yokohama', 'yoshi', 'you', 'young', 'youraccount', 'yournet', 'youth',
'youtrack', 'youtube', 'yp', 'yt', 'yty', 'yu', 'yx', 'z', 'z-hcm.nhac',
'z-hn.nhac', 'z-log', 'za', 'zabbix', 'zagreb', 'zakaz', 'zaq', 'zcvbnnn',
'zebra', 'zen', 'zenoss', 'zentrack', 'zenwalk', 'zephyr', 'zera', 'zero',
'zeta', 'zeus', 'zh', 'zimbra', 'zinc', 'zion', 'zip', 'zipkin', 'zippy', 'zj',
'zlog', 'zm', 'zmail', 'zoho', 'zoo', 'zoom', 'zos', 'zp', 'zs', 'zsb', 'zt',
'zulu', 'zvm', 'zvse', 'zw', 'zx', 'zy', 'zz', 'zzb', 'zzz'
]


def usage():
  print('\n' + USAGE)
  sys.exit()

  return


def check_usage():
  if len(sys.argv) == 1:
    print('[!] WARNING: use -H for help and usage')
    sys.exit()

  return


def get_default_nameserver():
  print('[+] getting default nameserver')
  lines = list(open('/etc/resolv.conf', 'r'))
  for line in lines:
    line = line.strip()
    if not line or line[0] == ';' or line[0] == '#':
      continue
    fields = line.split()
    if len(fields) < 2:
      continue
    if fields[0] == 'nameserver':
      defaults['nameserver'] = fields[1]
      return defaults

  return


def get_default_source_ip():
  print('[+] getting default ip address')
  try:
    # get current used iface enstablishing temp socket
    ipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ipsocket.connect(("gmail.com", 80))
    defaults['ipaddr'] = ipsocket.getsockname()[0]
    print('[+] found currently used interface ip ' + "'" + defaults['ipaddr'] \
      + "'")
    ipsocket.close()
  except:
    print(''' [!] WARNING: can\'t get your ip-address, use "-i" option and
      define yourself''')

  return defaults


def parse_cmdline():
  p = argparse.ArgumentParser(usage=USAGE, add_help=False)
  p.add_argument(
    '-t', metavar='<type>', dest='type',
    help='attack type (0 for dictionary 1 for bruteforce)'
  )
  p.add_argument(
    '-a', metavar='<domain>', dest='domain', help='subdomain to bruteforce'
  )
  p.add_argument(
    '-l', metavar='<wordlist>', dest='wordlist',
    help='wordlist, one hostname per line (default: built-in)'
  )
  p.add_argument(
    '-d', metavar='<nameserver>', dest='dnshost',
    help="choose another nameserver (default: your system's)"
  )
  p.add_argument(
    '-i', metavar='<ipaddr>', dest='ipaddr',
    help="source ip address to use (default: your system's)"
  )
  p.add_argument(
    '-p', metavar='<port>', dest='port', type=int, default=0,
    help='source port to use (default: 0 -> first free random port)'
  )
  p.add_argument(
    '-u', metavar='<protocol>', dest='protocol', default='udp',
    help='speak via udp or tcp (default: udp)'
  )
  p.add_argument(
    '-c', metavar='<charset>', dest='charset', default=0,
    help='choose charset 0 [a-z0-9], 1 [a-z] or 2 [0-9] (default: 0)'
  )
  p.add_argument(
    '-m', metavar='<maxchar>', dest='max', type=int, default=2,
    help='max chars to bruteforce (default: 2)'
  )
  p.add_argument(
    '-s', metavar='<prefix>', dest='prefix',
    help="prefix for bruteforce, e.g. 'www'"
  )
  p.add_argument(
    '-g', metavar='<postfix>', dest='postfix',
    help="postfix for bruteforce, e.g. 'www'"
  )
  p.add_argument(
    '-o', metavar='<sec>', dest='timeout', default=3,
    help='timeout (default: 3)'
  )
  p.add_argument(
    '-v', action='store_true', dest='verbose',
    help='verbose mode - prints every attempt (default: quiet)'
  )
  p.add_argument(
    '-w', metavar='<sec>', dest='wait', default=0,
    help='seconds to wait for next request (default: 0)'
  )
  p.add_argument(
    '-x', metavar='<num>', dest='threads', type=int, default=32,
    help='number of threads to use (default: 32) - choose more :)'
  )
  p.add_argument(
    '-r', metavar='<logfile>', dest='logfile', default='stdout',
    help='write found subdomains to file (default: stdout)'
  )
  p.add_argument(
    '-V', action='version', version='%(prog)s ' + VERSION,
    help='print version information'
  )
  p.add_argument('-H', action='help', help='print this help')

  return(p.parse_args())


def check_cmdline(opts):
  if not opts.type or not opts.domain:
    print('[-] ERROR: mount /dev/brain')
    sys.exit()

  return


def set_opts(defaults, opts):
  if not opts.dnshost:
    opts.dnshost = defaults['nameserver']
  if not opts.ipaddr:
    opts.ipaddr = defaults['ipaddr']
  if int(opts.charset) == 0:
    opts.charset = chars + digits
  elif int(opts.charset) == 1:
    opts.charset = chars
  else:
    opts.charset = digits
  if not opts.prefix:
    opts.prefix = prefix
  if not opts.postfix:
    opts.postfix = postfix

  return opts


def read_hostnames(opts):
  print('[+] reading hostnames')
  if opts.wordlist:
    with open(opts.wordlist, 'r') as f:
      return [x.rstrip() for x in f.readlines()]
  else:
    return wordlist

  return


def attack(opts, hostname):
  if opts.verbose:
    sys.stdout.write('    > trying %s\n' % hostname)
    sys.stdout.flush()
  try:
    x = dns.message.make_query(hostname, 1)
    if opts.protocol == 'udp':
      a = dns.query.udp(x, opts.dnshost, float(opts.timeout), 53, None,
        opts.ipaddr, opts.port, True, False)
    else:
      a = dns.query.tcp(x, opts.dnshost, float(opts.timeout), 53, None,
        opts.ipaddr, opts.port, False)
  except dns.exception.Timeout:
    sys.exit()
  except socket.error:
    print('''[-] ERROR: no connection? ip|srcport incorrectly defined? you can
           run only one thread if fixed source port specified!''')
    sys.exit()
  if a.answer:
    answ = ''
    # iterate dns rrset answer (can be multiple sets) field to extract
    # detailed info (dns and ip)
    for i in a.answer:
      answ += str(i[0])
      answ += ' '
    answer = (hostname, answ)
    found.append(answer)
  else:
    pass

  return


def prepare_attack(opts, hostnames):
  sys.stdout.write('[+] attacking \'%s\' via ' % opts.domain)
  if opts.type == '0':
    sys.stdout.write('dictionary... please wait!\n')
    with ThreadPoolExecutor(opts.threads) as exe:
      for hostname in hostnames:
        hostname = hostname.rstrip() + '.' + opts.domain
        time.sleep(float(opts.wait))
        exe.submit(attack, opts, hostname)
  elif opts.type == '1':
    sys.stdout.write('bruteforce\n')
    with ThreadPoolExecutor(opts.threads) as exe:
      for hostname in itertools.product(opts.charset, repeat=opts.max):
        time.sleep(float(opts.wait))
        hostname = opts.prefix + ''.join(hostname) + opts.postfix + '.' + \
          opts.domain
        exe.submit(attack, opts, hostname)
  else:
    print('[-] ERROR: unknown attack type')
    sys.exit()

  print()

  return


def ip_extractor(ip):
  # extract ip from string of rrset answer object
  try:
    extracted = re.findall(r'[0-9]+(?:\.[0-9]+){3}', ip)
    return extracted[0]
  except:
    print('[-] ERROR: can\'t extract ip addresses')
    sys.exit()

  return


def analyze_results(opts, found):
  # get maindomain ip
  try:
    mainhostip = socket.gethostbyname(opts.domain)
    # append domain|ip to diffound if subdomain ip different than starting
    # domain ip
    ([diffound.append(domain + ' | ' + ip) \
      for domain, ip in found if ip_extractor(ip) != mainhostip])
  except dns.exception.Timeout:
    sys.exit()
  except socket.error:
    print('[-] ERROR: wrong domain or no connection?')
    sys.exit()

  return


def log_results(opts, found, diffound):
  if opts.logfile == 'stdout':
    print('---')
    if not found:
      print('no hosts found :(')
    else:
      print('ANSWERED DNS REQUESTS')
      print('---')
      for f in found:
        print(f[0] + ' | ' + f[1])
    if not diffound:
      print('---')
      print('NO HOSTS WITH DIFFERENT IP FOUND :(')
    else:
      print('---')
      print('ANSWERED DNS REQUEST WITH DIFFERENT IP')
      print('---')
      for domain in diffound:
        print(domain)
  else:
    print('[+] logging results to %s' % opts.logfile)
    with open(opts.logfile, 'w') as f:
      if found:
        for x in found:
          f.write(x[0] + '\n')
      if diffound:
        for domain in diffound:
          f.write(domain + '\n')
  print('[+] game over')

  return


def main():
  check_usage()
  opts = parse_cmdline()
  check_cmdline(opts)
  if not opts.dnshost:
    defaults = get_default_nameserver()
  if not opts.ipaddr:
    defaults = get_default_source_ip()
  if opts.protocol != 'udp' and opts.protocol != 'tcp':
    print('[-] ERROR: unknown protocol')
    sys.exit(1337)
  opts = set_opts(defaults, opts)
  hostnames = read_hostnames(opts)
  prepare_attack(opts, hostnames)
  #analyze_results(opts, found)
  log_results(opts, found, diffound)

  return


if __name__ == '__main__':
  try:
    print(BANNER + '\n')
    main()
  except KeyboardInterrupt:
    print('\n[!] WARNING: aborted by user')
    raise SystemExit


# EOF
