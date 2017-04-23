# 使用說明

因使用方法日益增多，故將採用網頁式的說明讓使用者查看，因此，使用說明將暫時不更新，功能更新則會持續。部分內容可能因此不準確、有誤，操作時如和說明書內所寫有出入的話，還請見諒。

## 貼圖分析
對著小水母張貼貼圖將會顯示如下列資訊: 

```
Package ID: 1117417
Sticker ID: 4797205
```
```
Picture Location on Android(png):
emulated\0\Android\data\jp.naver.line.android\stickers\1117417\4797205
```
```
Picture Location on Windows PC(png):
C:\Users\USER_NAME\AppData\Local\LINE\Data\Sticker\1117417\4797205
```
```
Picture Location on Web(png):
https://sdl-stickershop.line.naver.jp/stickershop/v1/sticker/4797205/android/sticker.png
```

> - 回覆的第一則訊息會顯示貼圖的圖包ID(Package ID)和貼圖本身的ID(Sticker ID)。貼圖ID可以用在回覆組回覆時使用貼圖。
> - 第二、三則訊息則是圖片在Android手機或是Windows系統的電腦中，貼圖圖片檔案所在位置。
> - 第四則訊息則是貼圖在網路上的位址(URL)。如果是動圖的話，此位址則是動圖的最後模樣。

<hr>

`JC (指令) [參數1] [參數2] [參數3]...`
> - 每一個字組之間間隔2個空格
> - [錯誤訊息](#error)

### 權限分級

| 等級 | 說明 |
| :---: | :---: |
| 0 | 一般 |
| 1 | 群組總管 |
| 2 | 群組副管 |
| 3 | 機器人總管 |

### 聊天頻道代碼

| 英文簡寫 | 英文全名 | 中文解說 | 人數 |
| :---: | :---: | :---: | :---: |
| C | Chat | 一對一聊天 | 2 |
| R | Room | 房間(無須邀請) | 1+ |
| G | Group | 群組(需要邀請) | 1+ |

## 指令表

| 指令 | 全名 | 中文意義 | 權限等級 | 範例 | 備註 | 快轉 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `A` | **A**DD | 新增回覆組 | 0+ | `JC  A  水母  大水母` | | [連結](#a) |
| `D` | **D**ELETE | 刪除回覆組 | 0+ | `JC  D  水母`<br>`JC  D  ID  110` | | [連結](#d) |
| `Q` | **Q**UERY | 查詢回覆組 | 0+ | `JC  Q  水母`<br>`JC  Q  11  25` | 最多一次15組 | [連結](#q) |
| `I` | **I**NFO | 查詢回覆組的詳細資訊 | 0+ | `JC  I  水母`<br>`JC  I  ID  10` | 超過3組時會縮短 | [連結](#i) |
| `K` | RAN**K**ING | 關鍵字排行榜 | 0+ | `JC  K  10` | | [連結](#k) |
| `P` | S**P**ECIAL | 特殊小水母相關紀錄 | 0+ | `JC  P` | | [連結](#p) |
| `H` | C**H**ANNEL ID | 獲取ID | 0+ | `JC  H` | | [連結](#h) |
| `SHA` | **SHA**224 | 獲取SHA224加密字串 | 0+ | `JC  SHA  水母` | | [連結](#sha) |
| `S` | **S**QL | 直接指令 | 3+ | `JC  S  __  __` | | [連結](#s) |
| `M` | **M**AKE | 新增高級回覆組 | 2+ | `JC  M  水母  大水母  __` | 參數3為密鑰 | [連結](#m) |
| `R` | **R**EMOVE | 刪除高級回覆組 | 3+ | `JC  R  水母  __` | | [連結](#r) |
| `C` | **C**REATE | 建立關鍵字表格 | 3+ | `JC  C  {KEY}` | 平時不使用 | [連結](#c) |
| `G` | **G**ROUP | 群組靜音狀態查詢 | 0 | `JC  G` | | [連結](#g)
| `GA` | **G**ROUP ADVANCE | 群組靜音管理 | 1+ | (參見詳細) | | [連結](#ga)
| `O` | **O**XFORD | 牛津字典 | 0 | `JC  O  ace` | | [連結](#o)
| `B` | **B**YE | 退出房間、群組 | 0 | `JC  B` | | [連結](#b)

# 詳細使用說明
## A
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | × | × |

以下範例代表新增【收到"水母"時，回覆"大水母"】的回覆組。
```
JC  A  水母  大水母
```
 - **水母**為參數1(關鍵字)
 - **大水母**為參數2(回覆)

<hr>

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Pair Added. Total: 1
ID: 174
Keyword: 水母
Reply: 大水母
```
> - Keyword 代表 關鍵字
> - Reply 代表 回覆

<hr>

以下範例代表新增【收到"水母"時，回覆貼圖ID為4797205】的回覆組。
```
JC  A  水母  STK  4797205
```
 - **水母**為參數1(關鍵字)
 - **STK**為參數2，固定字STK代表回覆貼圖
 - **4797205**為參數3(貼圖ID)，[查詢貼圖ID方式請點此](#貼圖分析)
 
 <hr>

 輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Pair Added. Total: 1
ID: 174
Keyword: 水母
Reply Sticker ID: 4797205
```
> - Keyword 代表 關鍵字
> - Reply Sticker ID 代表 回覆貼圖ID號碼
> - 在下一則訊息則會顯示貼圖png檔案。

## D
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表刪除【所有收到"水母"時會用】的回覆組。請注意，為了留存紀錄，資料庫**並不會**真的刪除紀錄，只是更改一個欄位，讓小水母在偵測並回覆時不會使用。
```
JC  D  水母
```
 - **水母**為參數1(關鍵字)

<hr>

以下範例代表刪除【ID為110】的回覆組。請注意，為了留存紀錄，資料庫**並不會**真的刪除紀錄，只是更改一個欄位，讓小水母在偵測並回覆時不會使用。
```
JC  D  ID  110
```
 - `ID`為參數1，固定字
 - **110**為參數2(ID)

<hr>

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Pair below DELETED.
ID: 174
Keyword: 水母
Reply: 大水母
This pair is created by 狼兒專屬水母醬 - D-78.
```
> - Keyword 代表 關鍵字
> - Reply 代表 回覆
> - Created by 代表 由...製作
## Q
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表搜尋含有水母的關鍵字或回覆。
```
JC  Q  水母
```
 - **水母**為參數1(搜尋關鍵字)

<hr>

以下範例代表搜尋ID介於101到115之間的關鍵字。
```
JC  Q  101  115
```
 - **101**為參數1(起始ID)
 - **115**參數2(終止ID)

<hr>

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Keyword found. Total: 7. Listed below.
ID: 163 - 小水母乖乖 
ID: 26 - 水母經 
ID: 174 - 水母 (DEL)
ID: 5 - 水母 (OVR)(DEL)(TOP)
ID: 52 - 烤水母 
ID: 46 - 水母 (OVR)(DEL)
ID: 59 - 炸水母
```
> - 上方會顯示索引結果數量，`Total: n.` 代表索引到n個結果。
> - (OVR)全名為OVERRIDE，亦即被覆蓋，偵測到對應關鍵字時**並不會**使用該回覆組的回覆。
> - (DEL)全名為DELETED，亦即已刪除，偵測到對應關鍵字時**並不會**使用該回覆組的回覆。
> - (TOP)全名為TOP PAIR，亦即置頂指令，需要使用高權限指令才可以[新增](#m)或[刪除](#r)，此字組不會被一般自組覆蓋(OVERRIDE)，只會被同級字組覆蓋。
## I
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表要求顯示所有回覆組中，關鍵字或回覆包含「水母」的詳細資訊。<br>此語法一次可能顯示非常多字組(包含已覆蓋和使用中)。為了避免洗版，使用此種使用法時若回傳結果超過3組，將只會顯示基本資訊，要詳細資訊的話請用ID搜尋。
```
JC  I  水母
```
 - **水母**為參數1(查詢字)

<hr>

以下範例代表搜尋ID為87的關鍵字。此語法一次最多只會顯示一個字組。
```
JC  I  ID  87
```
 - 固定字`ID`為參數1
 - **87**為參數2(ID)

<hr>

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
ID: 174
Keyword: 水母
Reply: 大水母
Override: False
Admin Pair: False
Has been called 0 time(s).
Created by 狼兒專屬水母醬 - D-78.
ID: 5
Keyword: 水母
Reply: LINE ID: chris80124
Override: True
Admin Pair: True
Has been called 0 time(s).
Created by 狼兒專屬水母醬 - D-78.
```

> - Keyword 代表 關鍵字
> - Reply 代表 回覆
> - Override 代表 覆蓋，True為真(已覆蓋)；False為假(未覆蓋)
> - Admin Pair 代表 高級字組，True為是；False為否
> - Has been called n time(s). 代表 已經使用該字組回覆n次。當字組被覆蓋或刪除以後，便會停止計數。
> - Created by 代表 由...製作
## K
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表顯示回覆次數前10名的關鍵字。
```
JC  K  10
```
 - **10**為參數1(名次)

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
KEYWORD CALLING RANKING (Top 10)

No.1 - 哈哈 (ID: 101, 24 times.)
No.2 - 歐洲人 (ID: 66, 12 times.)
No.3 - ... (ID: 106, 9 times.)
No.4 - 水母 (ID: 46, 8 times.)
No.5 - 亞絲娜 (ID: 81, 8 times.)
No.6 - 恩 (ID: 57, 7 times.)
No.7 - 哈哈哈 (ID: 94, 7 times.)
No.8 - 派大 (ID: 123, 6 times.)
No.9 - 真的 (ID: 152, 6 times.)
No.10 - Lacus (ID: 170, 6 times.)
```
## P
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表顯示小水母相關統計數據。
```
JC  P
```
 - 此功能沒有參數


輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Boot up Time: 2017-03-25 19:15:53.205354 (UTC)
Count of Keyword Pair: 159
Count of Reply: 250
Most Creative User:
林志陽 (53 Pairs)
Most Popular Keyword:
哈哈 (ID: 101, 24 Time(s))
Most Unpopular Keyword:
平偉 (ID: 166, 0 Time(s))

System command called time (including failed): 8
Command 'M' Called 0 Time(s).
Command 'H' Called 0 Time(s).
Command 'I' Called 1 Time(s).
Command 'K' Called 1 Time(s).
Command 'D' Called 1 Time(s).
Command 'G' Called 0 Time(s).
Command 'SHA' Called 0 Time(s).
Command 'A' Called 1 Time(s).
Command 'C' Called 0 Time(s).
Command 'P' Called 1 Time(s).
Command 'Q' Called 1 Time(s).
Command 'R' Called 0 Time(s).
Command 'S' Called 0 Time(s).
```
> - Boot up Time 代表 開機時間，該時間為國際標準時間(UTC)，港澳台區使用者請自行+8小時(UTC+8)。
> - Count of Keyword Pair 代表 目前資料庫總收錄字組數量
> - Count of Reply 代表 目前已使用字組回覆的字次數
> - Most Creative User 代表 目前製作最多關鍵字的使用者
> - Most Popular Keyword 代表 目前回覆次數最多的字組
> - Most Unpopular Keyword 代表 目前最冷門的字
> - System command called time (including failed) 代表 目前已經呼叫系統指令的次數(包含呼叫失敗)
## H
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表獲取當前聊天頻道ID。
```
JC  H
```
 - 這個指令沒有參數

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Type: User
```
```
Ud5a2b5bb5eca86342d3ed5e31d606e2c
```
> 為了[指令GA](#ga)使用方便，本指令抓取ID時特別使用兩則訊息發送。第二則訊息為ID，固定33字元長。<br>在不同的地方(chat、group、room)中輸入此指令時，種類(Type)和ID頭一碼，參見下表和最上方聊天頻道表: 

| 英文 | ID頭一碼 |
| :---: | :---: |
| chat | U |
| group | C |
| room | R |

## SHA
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表獲取**水母**的SHA-224加密字串。
```
JC  SHA  水母
```
 - **水母**為參數1(加密對象)

輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
13ca32d99a4d3a445780b8b76848a32f05f6d20c4656f947117daa42
```
> 此加密為不可逆性的加密，是一種雜湊加密，[詳情請點此](https://zh.wikipedia.org/wiki/SHA-2)
## S
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | × | × |

系統直接指令。於參數1輸入指令，參數2輸入密鑰。
## M
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | × | × |

新增高階回覆組。於參數1輸入密鑰，參數2輸入關鍵字，參數3輸入回覆。
## R
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | × | × |

刪除高階回覆組。於參數1輸入關鍵字，參數2輸入密鑰。
## C
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

建立關鍵字表格，參數1輸入密鑰，平時不使用。
## G
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表顯示群組相關資訊。
```
JC  G
```
輸入後，如果該群組沒有登記管理的話，就會顯示類似如下的回覆:
```
Group ID: C11f852e4612807ab02bf9a6e7f102c74
Silence: False
```
反之，群組已經登記管理員的話，就會顯示: 
```
Group ID: Ce74a1c79c00d83d204bad1e057bac46b
Silence: False

Admin: 狼兒專屬水母醬 - D-78
Admin User ID: Ud5a2b5bb5eca86342d3ed75d1d606e2c
```
> - Silence: False 代表 自動回覆功能運作中
> - Silence: True 代表 自動回覆功能已關閉
## GA
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | × | × |

請注意，每個指令都有權限限制，限制級別相關事項，請參考最上方的說明，每個指令後方的括號在輸入時無需輸入，其中內容代表最低存取權限要求。

請記牢自訂密鑰、權限密鑰，日後管理群組時會用到！

<hr>

在每個GA指令下達後的回覆一定是以下文字:
```
Permission: {YOUR_PERMISSION}
```
YOUR_PERMISSION 共有四種，分別代表四種權限: 

| 顯示(英文) | 中文 | 對應權限等級(參見最上方) |
| :---: | :---: | :---: |
| Bot Administrator | 機器人管理員 | 3 |
| Group Admin | 群組管理員 | 2 |
| Group Moderator | 群組副管 | 1 |
| User | 一般使用者 | 0 |

### 建立群組靜音資料表
以下範例代表建立群組靜音資料表。
```
JC  GA  abc  C (3+)
```
 - **abc**為參數1，代表權限密鑰(需向管理員拿取)
 - `C`為參數2，固定字

### 建立群組靜音資料
以下範例代表建立群組靜音管理員的資料。
```
JC  GA  abc  N  Cffffff  Uffffff  abcdefg (3+)
```
 - **abc**為參數1，代表權限密鑰(需向管理員拿取)
 - `N`為參數2，固定字
 - **Cfffff**為參數3(群組ID)，長度固定33字元，可以藉由[指令G](#g)獲得ID
 - **Ufffff**為參數4(使用者ID)，長度固定33字元，可以藉由[指令H](#h)獲得ID
 - **abcdefg**為參數5(自訂密鑰)

### 更改群組靜音設定
以下範例代表更改群組靜音設定
```
JC  GA  abc  ST  Cffffff  abcdefg (1+)
```
 - **abc**為參數1，代表權限密鑰(需向管理員拿取)
 - `ST`為參數2，指令，ST代表開啟自動回覆、SF代表關閉自動回覆
 - **Cfffff**為參數3(群組ID)，長度固定33字元，可以藉由[指令G](#g)獲得ID
 - **abcdefg**為參數4(自訂密鑰)

### 更改群組管理員/副管理員
群組管理源和副管理員都可以更改群組靜音設定，差異在於管理員可以更動權限(讓渡、退管)，副管理員則只能更動功能開關。

以下範例代表建立群組靜音管理員的資料。
```
JC  GA  abc  SA  Cffffff  Uffffff  abcdefg hijklmn
```
 - **abc**為參數1，代表權限密鑰(需向管理員拿取)
 - `SA`為參數2，指令，SA代表更動管理員、SM1、2、3代表更動副管1、副管2、副管3
 - **Cfffff**為參數3(群組ID)，長度固定33字元，可以藉由[指令G](#g)獲得ID
 - **Ufffff**為參數4(新管理員/副管)，長度固定33字元，可以藉由[指令H](#h)獲得ID
 - **abcdefg**為參數5(原自訂密鑰)
 - **hijklmn**為參數6(新自訂密鑰)

## O
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表查詢單字 - **jellyfish**。
```
JC  O  jellyfish
```
 - **jellyfish**為參數1(查詢單字)

輸入後，有兩種回覆，分別是有結果和無結果，如下所列: 

(無結果)
```
Dictionary look up process returned status code: 404 (Not Found).
```
> - **404**是HTTP代碼。
> - **Not Found**是HTTP代碼的解說。
> - [詳細HTTP代碼說明請點此(英文)](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)

(有結果)
```
Powered by Oxford Dictionary.

jellyfish (Noun)
Definition: 
1. a free-swimming marine coelenterate with a jelly-like bell- or saucer-shaped body that is typically transparent and has stinging tentacles around the edge.
2. a feeble person.
```
> - 第一行`Powered by Oxford Dictionary.`固定不變，代表來自牛津字典。
> - 第三行以後則是查詢結果。

>## B
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| × | ○ | ○ |

以下範例代表要求機器人離開群組、房間。
```
JC  B
```

輸入後，機器人將會回覆以下訊息並離開群組:
```
Leave Group: Cxxxxxx
Contact Link: http://line.me/ti/p/@fcb0332q
```
> - Cxxxxxx代表群組或房間ID，長度為33字元
> - 如果離開的是房間的話，**Leave Group**會變成**Leave Room**。

# Error

> 發生錯誤時，請先檢查所列錯誤，若檢查完畢後仍然沒有得到解決，請將紀錄截圖以後[傳到這裡](http://line.me/ti/p/~chris80124)

參數短缺，請檢察指令及其相關使用方法。
```
Lack of parameter(s). Please recheck your parameter(s) that correspond to the command.
```

無法在非聊天頻道使用指令，請使用chat輸入指令。
```
Unavailable to add keyword pair in GROUP or ROOM. Please go to 1v1 CHAT to execute this command.
```

不合法的指令{cmd}，請查閱使用說明。
```
Invalid Command: {cmd}. Please recheck the user manual.
```

API錯誤，通常由內容不合法造成。通常觸發原因非使用問題，若發生此問題請將對話記錄截下，[傳到這裡](http://line.me/ti/p/~chris80124)
```
Line Bot Api Error. Status code: {sc}
```

指令不合。錯誤的指令參數組合，或是權限不足。
```
No command fetched.
Wrong command, parameters or insufficient permission to use the function.
```

此功能只可以在chat中操作，並且需要權限才可以執行。
```
This function can be used in 1v1 CHAT only. Permission key required. Please contact admin.
```
