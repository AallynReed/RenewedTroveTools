with open("locales/zh_CN.loc",'r',encoding='utf-8') as dataf:
    data = dataf.read()

result = ""
from translate import Translator
import langid
for line in data.splitlines():
    key,value = line.split("»»")
    if("❓" in value):
        value.strip('❓')
        if(langid.classify(value)[0] != "zh"):
            result += f"{key}»»❓{Translator(from_lang="EN-US",to_lang="ZH").translate(value)}\n"
        else:
            result +=f"{key}»»❓{value}\n"
    else:
        result += f"{key}»»{value}\n"
    print(f"{len(result.splitlines())}/{len(data.splitlines())}")

with open("Temp/temp.loc",'w',encoding='utf-8') as dataf:
    dataf.write(result)