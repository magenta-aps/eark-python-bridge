import os
import os.path

path = '/pre-SIP/representations/rep1/data/dmjx-guide/documentLibrary/Love'
prefix_path = '/home/andreas/eark/dmjx'

folders = path.split('/')[1:]

current_path = prefix_path
current_dict = {'name': os.path.basename(current_path), 'path': current_path}
for folder in folders:
    print 25*'#'
    print folder
    
    current_path = os.path.join(current_path, folder)
    print current_path
    
    
    folders_in_current_path = [f for f in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, f))]
    if not len(folders_in_current_path) == 0:
        d = None
        children = []
        for f in folders_in_current_path:
            name_path_dict = {'name': f, 'path': os.path.join(current_path, f)}
            if f == 
            children.append(name_path_dict)
        


    raise
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