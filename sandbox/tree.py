import sys
import os.path
from pprint import pprint
# path = '/pre-SIP/representations/rep1/data/dmjx-guide/documentLibrary/Love'
# prefix_path = '/home/andreas/eark/dmjx'

# path = '/testip/representations/rep1/data/c/g'
#path = '/testip/representations'
#path = '/testip'
path = sys.argv[1]
prefix_path = '/home/andreas/magenta/eark-python-bridge/sandbox'


def gettree(path, prefix_path):
    folders = path.split('/')[1:]
    print 'folders =', folders
    
    
    current_path = os.path.join(prefix_path, folders[0])
    tree = {'name': os.path.basename(current_path), 'path': current_path, 'type':'folder'}
    current_dict = tree
    
    print 'len(folders) =', len(folders)
    for i in range(len(folders)):
        print 25*'#'
        print 'i =', i
        print folders[i]
        
        # current_path = os.path.join(current_path, folders[i])
        print current_path
        
        if i < len(folders) - 1: 
            items_in_current_path = [f for f in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, f))]
        else:
            items_in_current_path = os.listdir(current_path)
        print 'items in current path = ', items_in_current_path

        if not len(items_in_current_path) == 0:
            children = []
            if i < len(folders) - 1:
                # Not at the leaf folder
                for f in items_in_current_path:
                    name_path_dict = {'name': f, 'path': os.path.join(current_path, f), 'type': 'folder'}
                    print name_path_dict
                    if f == folders[i + 1]:
                        d = name_path_dict 
                    children.append(name_path_dict)
                current_dict['children'] = children
                current_dict = d
                print 'current dict =', current_dict
                current_path = os.path.join(current_path, d['name'])
            else:
                # At the leaf folder
                for f in items_in_current_path:
                    name_path_dict = {'name': f, 'path': os.path.join(current_path, f)}
                    if os.path.isdir(name_path_dict['path']):
                        name_path_dict['type'] = 'folder'
                    else:
                        name_path_dict['type'] = 'file'
                    print name_path_dict
                    children.append(name_path_dict)
                current_dict['children'] = children
                
    return tree



# TO-DO: the recursive way...

def f(tree, path, list_of_folders):

    if not len(list_of_folders) == 0:
        current_folder = list_of_folders.pop[0]
        new_path = os.path.join(path, current_folder)
        
        print new_path
    else:
        pass
    
    

def _gettree(path, prefix_path):
    folders = path.split('/')[1:]
    print 'folders =', folders

    tree = {}
    f(tree, prefix_path, folders)
    
    

    current_path = os.path.join(prefix_path, folders[0])
    tree = {'name': os.path.basename(current_path), 'path': current_path}
    current_dict = tree
    
    




result = gettree(path, prefix_path)
print 25*'-'
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