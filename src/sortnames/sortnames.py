'''
Created on Jul 31, 2015

@author: jrl
'''
import fileinput

if __name__ == '__main__':
    contribs = {}
    for line in fileinput.input():
        fields = line.split('\t')
            
        # Use the login name if real name is missing
        if fields[1] == '':
            login = fields[0]
            name = login
            if login == 'jackbackrack':
                name = 'Jonathan Bachrach'
            elif login == 'kasanovic':
                name = 'Krste Asanovic' 
            fields[1] = name
        elif fields[1] == 'Donggyu':
            fields[1] = 'Donggyu Kim'
        name = fields[1]
        (first, sep, last) = name.rpartition(' ')
        key = last.lower()
        contribs[key] = fields[1]
    for key in sorted(contribs.iterkeys()):
        if False:
            print '  <tr>\n    <td>\n      %s\n    </td\n    <td>\n\n    </td>\n  </tr>' % (contribs[key])
        else:
            print '| %s |  | ' % (contribs[key])
