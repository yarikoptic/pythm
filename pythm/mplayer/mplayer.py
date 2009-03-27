import os
import select
import subprocess
import time
import sys
from threading import Lock

from pythm.config import PythmConfig

#http://code.activestate.com/recipes/542195/

class MPlayer(object):
    """ A class to access a slave mplayer process
    you may want to use command(name, args*) directly
    or call populate() to access functions (and minimal doc).

    Exemples:
        mp.command('loadfile', '/desktop/funny.mp3')
        mp.command('pause')
        mp.command('quit')

    Note:
        After a .populate() call, you can access an higher level interface:
            mp.loadfile('/desktop/funny.mp3')
            mp.pause()
            mp.quit()

        Beyond syntax, advantages are:
            - completion
            - minimal documentation
            - minimal return type parsing
    """

    def __init__(self,path=None,niceval=None):
        if path is None:
            path = 'mplayer' if os.sep == '/' else 'mplayer.exe'

        args = [path, '-slave', '-quiet', '-idle', '-nolirc', '-osdlevel', '0']
        self._mplayer = subprocess.Popen(args,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
        
        if self._mplayer and niceval!=None:
            pid = self._mplayer.pid
            os.system("renice "+ str(niceval) +" -p "+str(pid))
        
        self.lock = Lock()

    def command(self,cmd,*args):
        """
        a command that does not read anything
        """
        return self._cmd(cmd,None,*args)
    
    def cmd(self,name,key,*args):
        """
        single line reading with key
        """
        return self._cmd(name,key,*args)
    
    def quit(self):
        self.command("quit",0)
        self._mplayer.wait()
    
    def _cmd(self,name,key,*args):
        """
        key is the beginning of a line that the command waits for.
        if it is None, the read from mplayers stdout will be omitted.
        if readall is true, all is read until a line begins with key.
        """
        cmd = '%s%s%s\n'%(name,
                ' ' if args else '',
                ' '.join(repr(a) for a in args)
                )       
        return self.innercmd(cmd,key)
         
    def innercmd(self,cmd,key):
        
        ret = None
        
        self.lock.acquire()  
        i = 0      
        try:
	    #print ""
            #print "CMD : " + str(cmd)
            self._mplayer.stdin.write(cmd)
            if key != None:
                #while any(select.select([self._mplayer.stdout.fileno()], [], [], 20)):
                while any(select.select([self._mplayer.stdout.fileno()], [], [], 1)):
                    tmp = self._mplayer.stdout.readline()
                    #print "MPLAYER: " +str(cmd).strip() + " : " + tmp.strip()
                    if tmp.startswith(key):
                        val = tmp.split('=', 1)[1].rstrip()
                        try:
                            ret = eval(val)
                        except:
                            ret = val
                        break
        except Exception,e:
            print "error in mplayer.innercmd: "+str(e)
	    ret = None
            pass
        
        self.lock.release()

        return ret

