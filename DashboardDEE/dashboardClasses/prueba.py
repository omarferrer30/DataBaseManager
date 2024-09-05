from ttkwidgets import CheckboxTreeview
import tkinter as tk

root = tk.Tk()

tree = CheckboxTreeview(root)
tree.pack()
"""tree['column'] = ('wp', 'latitude', 'longitude')
tree.column("wp", anchor=tk.CENTER, width=10)
tree.column("latitude", anchor=tk.CENTER, width=40)
tree.column("longitude", anchor=tk.CENTER, width=40)

tree.heading("wp", text="wp" )
tree.heading("latitude", text="Latitude")
tree.heading("longitude", text="Longitude")

tree.insert(parent='',   index='end', id=0, values=('H', 'AAA', 'BBB'))
tree.insert(parent='',    index='end',id=1, values=('H', '1111', 'BBB'))
tree.insert(parent='', index='end',id=2,  values=('H', '2222', 'BBB'))
tree.insert(parent='', index='end', id=3, values=('H', '3333', 'BBB'))
tree.insert(parent='', index='end', iid=4, values=('H', '4444', 'BBB'))"""
id = 1
lat = 41.12345678
lon = 1.91234567
num = 41.123456789

tree.insert("", "end", iid=1, text="{0}\t{1:10}, {2:10}".format(id, lat, lon))
tree.insert("", "end", iid=2, text="{0}\t{1}, {2}".format(111, lat, lon))
entries = tree.get_children()
entry = [en for en in entries if str(tree.item(en)["text"].split("\t")[0]) == str(111)]

location = tree.item(entry)["text"].split("\t")[1].split(",")
lat = float(location[0])
lon = float(location[1])
print("lo que buscas es: ", lat, lon)

res = str(1).rjust(1 + len(str(1)), "0")
print(res)

root.mainloop()
