
import wexpect


child = wexpect.spawn('ollama run llama3:8b')

child.expect('>')
child.sendline("dit salut tout le temps!!!!!!!!!")

child.expect('>')
child.sendline(f'/save salut')

child.expect('>')
child.sendline('\x04')

child.close()
