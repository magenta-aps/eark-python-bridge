import os
import os.path
from pprint import pprint
# path = '/pre-SIP/representations/rep1/data/dmjx-guide/documentLibrary/Love'
# prefix_path = '/home/andreas/eark/dmjx'

path = '/testip/representations/rep1/data/c/g'
prefix_path = '/home/andreas/eark/eark-python-bridge/sandbox'


def gettree(path, prefix_path):
    folders = path.split('/')[1:]
    print 'folders =', folders
    
    
    current_path = os.path.join(prefix_path, folders[0])
    tree = {'name': os.path.basename(current_path), 'path': current_path}
    current_dict = tree
    for i in range(len(folders)):
        print 25*'#'
        print folders[i]
        
        # current_path = os.path.join(current_path, folders[i])
        print current_path
        
        
        folders_in_current_path = [f for f in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, f))]
        if not len(folders_in_current_path) == 0:
    
            children = []
            for f in folders_in_current_path:
                name_path_dict = {'name': f, 'path': os.path.join(current_path, f)}
                print name_path_dict
                if f == folders[i + 1]:
                    d = name_path_dict 
                children.append(name_path_dict)
            current_dict['children'] = children
            current_dict = d
            print 'current dict =', current_dict
            current_path = os.path.join(current_path, d['name'])
    
    return tree

result = gettree(path, prefix_path)
pprint(result) 


    # raise
""" 
current_path = root
current = {name: root, path: root path}   
for folder in list of path folders:
  l = get list of all folders
  d = None
  l = []
  for f in l:
    temp = construct {name:..., path:...}
    if f is the next in line:
      d = temp
    add temp to l
  add l to current
  current = d
  current_path = current_path + ...
"""