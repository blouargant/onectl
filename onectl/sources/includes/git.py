from subprocess import Popen, PIPE
from os import path
import re
import gprint

pcolor = gprint.GraphicalPrinter()

def gitCheckForCommit(repoDir):

	cmd = 'git status -s'
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(git_status, error) = pipe.communicate()
	pipe.wait()
	if git_status:
		return True
	else:
		return False

def gitGetCommitSeqNum(repoDir):
	cmd = 'git rev-list HEAD --count'
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(commitSequenceNum, error) = pipe.communicate()
	pipe.wait()
	if error:
		commitSequenceNum=0
	return commitSequenceNum

def gitGetCommitIdBySeqNum(repoDir, seqNum):
	if not seqNum:
		cmd='git rev-list HEAD --count'
		pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
		(seqNum, error) = pipe.communicate()
		seqNum=int(seqNum)
		if seqNum>=2:
			seqNum-=2
		else:
			seqNum=0

	cmd = 'git log -g --grep="%s"'%seqNum + '  --pretty=format:"%h"'
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(commitId, error) = pipe.communicate()
	pipe.wait()
	if error:
		return None
	return commitId


def gitAdd(fileName, repoDir):
	cmd = ['git', 'add', fileName]
	p = Popen(cmd, cwd=repoDir)
	p.wait()

def gitCommit( repoDir):
	if not gitCheckForCommit(repoDir):
		return 
	commitSequenceNum = gitGetCommitSeqNum(repoDir)
	commitMessage="%s" %commitSequenceNum
	cmd = 'git commit -am "%s"'%commitMessage
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(out, error) = pipe.communicate()
	#print out,error
	pipe.wait()
	return 

def gitRevert(repoDir, commitId):
	cmd = 'git reset --hard %s'%commitId
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(out, error) = pipe.communicate()
	#print out,error
	pipe.wait()
	return 


def gitHistory(repoDir):
	MAX_PLUG_LEN = 44
	MAX_DATE_LEN = 16
	cmd = "git log -p --reverse --pretty=format:'---------------%nINFO::%ad::%an:: %B' --date=iso  -b --no-merges | grep -Ev '@@|^--- |^index|^diff|^\+\+\+|^new|^ '"
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(out, error) = pipe.communicate()
	pipe.wait()
	sections = out.split('---------------')
	break_line = '-------------------------------------------------------------------------------'
	head_line = pcolor.BOLD+'   ID'+pcolor.ENDC+' | '
	head_line += pcolor.BOLD+'Changeset'.ljust(MAX_PLUG_LEN)+pcolor.ENDC+' | '
	head_line += pcolor.BOLD+'Date and Time'+pcolor.ENDC+'    | '
	head_line +=pcolor.BOLD+'User '+pcolor.ENDC
	result = []
	result.append(head_line)
	for sec in sections:
		if not re.match('^$', sec.strip()):
			result.append(break_line)
			lines = sec.split('\n')
			changeset = []
			for line in lines:
				line = line.strip()
				if re.search('^INFO:', line):
					#INFO::2015-11-06 12:41:16 +0100::root:: 7
					infos = line.split('::')
					date_infos = infos[1].split(':')
					date = date_infos[0]+':'+date_infos[1]
					user = infos[2].strip()
					id = infos[3].strip()
				elif not re.match('^$', line):
					if len(line) > MAX_PLUG_LEN:
						args = line.split('=',1)
						akey = args[0].strip()
						config = args[1].split(' ')
						short_key = True
						first = True
						strMax = akey+' ='
						strMin = ''
						for a_cfg in config:
							if a_cfg:
								strMax += a_cfg
								if len(strMax) > MAX_PLUG_LEN:
									if not strMin:
										first = True
										strMin = akey+' ='
										changeset.append(strMin)
										short_key = False
									else:
										if short_key and not first:
											tmpline = akey+' =' + strMin
											#tmpline = ' '.ljust(len(akey+' ='))+strMin+' '
											changeset.append(tmpline)
										else:
											first = False
											changeset.append(' '+strMin)
									strMin = a_cfg
									strMax = a_cfg
								else:
									strMin = strMax
						if strMin:
							if short_key:
								#tmpline = ' '.ljust(len(akey+' = '))+strMin+' '
								tmpline = akey+' = ' + strMin
								changeset.append(tmpline)
							else:
								changeset.append(' '+strMin)
					else:
						changeset.append(line)
					
			if not changeset:
				if id == '0':
					tmpline = pcolor.BOLD+id.rjust(5)+pcolor.ENDC
					tmpline += ' | %s | %s | %s ' %('INITIALIZATION'.center(MAX_PLUG_LEN), date, user)
					#tmpline += ' | '+' '.ljust(14)+'INITIALIZATION'.ljust(28)
					#tmpline += ' | '+date+' | '+user
					result.append(tmpline)
				else:
					result.append(id.rjust(5)+' | '+' '.ljust(MAX_PLUG_LEN)+' | '+date+' | '+user)
			else:
				tmpline = pcolor.BOLD+id.rjust(5)+pcolor.ENDC
				tmpstr = changeset[0].ljust(MAX_PLUG_LEN)
				if len(tmpstr)>MAX_PLUG_LEN:
					tmpstr = tmpstr[:MAX_PLUG_LEN]
					
				if re.search('^\+', tmpstr):
					finalstr = pcolor.OKBLUE+'+'+pcolor.ENDC+pcolor.OKGREEN+re.sub('^\+', '', tmpstr)+pcolor.ENDC
				elif re.search('^-', tmpstr):
					finalstr = pcolor.OKBLUE+'-'+pcolor.ENDC+pcolor.OKGREEN+re.sub('^-', '', tmpstr)+pcolor.ENDC
				else:
					finalstr = pcolor.ENDC+pcolor.OKGREEN+tmpstr+pcolor.ENDC
				#tmpline += ' | '+finalstr
				#tmpline += ' | '+date+' | '+user
				tmpline += ' | %s | %s | %s' %(finalstr, date, user)
				result.append(tmpline)
				for newline in changeset[1:]:
					tmpline = ' '.rjust(5)
					tmpstr = newline.ljust(MAX_PLUG_LEN)
					if len(tmpstr)>MAX_PLUG_LEN:
						tmpstr = tmpstr[:MAX_PLUG_LEN]
					if re.search('^\+', tmpstr):
						finalstr = pcolor.OKBLUE+'+'+pcolor.ENDC+pcolor.OKGREEN+re.sub('^\+', '', tmpstr)+pcolor.ENDC
					elif re.search('^-', tmpstr):
						finalstr = pcolor.OKBLUE+'-'+pcolor.ENDC+pcolor.OKGREEN+re.sub('^-', '', tmpstr)+pcolor.ENDC
					else:
						finalstr = pcolor.ENDC+pcolor.OKGREEN+tmpstr+pcolor.ENDC
					#tmpline += ' | '+finalstr
					#tmpline += ' | '+' '.ljust(len(date))+' |'
					tmpline += ' | %s | %s |' %(finalstr, ' '.rjust(MAX_DATE_LEN))
					result.append(tmpline)
				
	output = '\n'.join(result)+'\n'
	return output

def gitShow(repoDir, commitId):
	if not commitId:
		commitId=''
	cmd="git show %s:onectl.data" %commitId
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(out, error) = pipe.communicate()
	pipe.wait()
	if error:
		return ''
	return out

def gitGetLastChanges(repoDir):
	output_dct = {}
	output_dct['changed']={}
	output_dct['deleted']={}
	output_dct['added']={}

	if not gitCheckForCommit(repoDir):
		return None
	
	cmd="git diff HEAD^1 | grep -Ev '@@|^---|^index|^diff|^\+\+\+|^new|^ '"
	pipe = Popen(cmd, shell=True, cwd=repoDir,stdout = PIPE,stderr = PIPE )
	(output, error) = pipe.communicate()
	pipe.wait()
	
	if error:
		return None
	# -sys.hostname = prometheusTest
	# +sys.hostname = prometheusTest1
	
	if not output:
		return
	lines = output.split('\n')
	for line in lines:
		line = line.strip()
		if not line:
			continue
	
		values = line.split('=', 1)
		key = values[0].strip()
		value = values[1].strip()
	
		if re.search('^\+', line):
			key = re.sub('^\+', '', key)
			output_dct['added'] = {key:value}
		elif re.search('^-', line):
			key = re.sub('^-', '', key)
			output_dct['deleted'] = {key:value}
		else:
			continue

	for key in dict(output_dct['added']):
		if key in output_dct['deleted']:
			output_dct['changed']= {key:output_dct['added'][key]}
			del output_dct['deleted'][key]
			del output_dct['added'][key]
	
	return output_dct

