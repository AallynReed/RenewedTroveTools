with open("locales/en_US.loc",'r',encoding='utf-8') as dataf:
    data = dataf.read()

with open("Temp/temp.loc",'w',encoding='utf-8') as dataf:
    dataf.write('\n'.join(sorted(data.splitlines(),key=lambda x: x.lower())))