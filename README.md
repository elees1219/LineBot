# 使用說明

JC  (指令)  [參數1]  [參數2]  [參數3]...
> 每一個字組之間間隔2個空格

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

| 指令 | 中文意義 | 權限等級 | 範例 | 備註 | 快轉 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `A` | 新增回覆組 | 0 | `JC  A  水母  大水母` | | [連結](#a) |
| `D` | 刪除回覆組 | 0 | `JC  D  水母` | | [連結](#d) |
| `Q` | 指定ID範圍的回覆組 | 0 | `JC  Q  11  25` | 一次最多呼叫15組關鍵字 | [連結](#q) |
| `I` | 指定的回覆組詳細資訊 | 0 |  `JC  I  水母` | | [連結](#i) |
| `K` | 關鍵字排行榜 | 0 | `JC  K  10` | | [連結](#k) |
| `P` | 特殊小水母相關紀錄 | 0 | `JC  P` | | [連結](#p) |
| `H` | 獲取ID | 0 | `JC  H` | | [連結](#h) |
| `SHA` | 獲取SHA224加密字串 | 0 | `JC  SHA  水母` | | [連結](#sha) |
| `S` | 直接指令 | 3 | `JC  S  __  __` | | [連結](#s) |
| `M` | 新增高級回覆組 | 3 | `JC  M  水母  大水母  __` | 參數3為密鑰 | [連結](#m) |
| `R` | 刪除高級回覆組 | 3 | `JC  R  水母  __` | | [連結](#r) |
| `C` | 建立關鍵字表格 | 0 | `JC  C` | 平時不使用 | [連結](#c) |
| `G` | 群組靜音管理 | 1+ | (尚未完成) | | [連結](#g)

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
**水母**為參數1(關鍵字)；**大水母**為參數2(回覆)。
輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Pair Added. Total: 1
ID: 174
Keyword: 水母
Reply: 大水母
```
> Keyword 代表 關鍵字
> Reply 代表 回覆
## D
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表刪除【收到"水母"時，回覆"大水母"】的回覆組。請注意，為了留存紀錄，資料庫**並不會**真的刪除紀錄，只是更改一個欄位，讓小水母在偵測並回覆時不會使用。
```
JC  D  水母
```
**水母**為參數1(關鍵字)。
輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Pair below DELETED.
ID: 174
Keyword: 水母
Reply: 大水母
This pair is created by 狼兒專屬水母醬 - D-78.
```
> Keyword 代表 關鍵字
> Reply 代表 回覆
> Created by 代表 由...製作
## Q
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表搜尋含有水母的關鍵字。
```
JC  Q  水母
```
**水母**為參數1(關鍵字)。
以下範例代表搜尋ID介於101到115之間的關鍵字。
```
JC  Q  101  115
```
**101**為參數1(起始ID)、**115**參數2(終止ID)。
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
> 上方會顯示索引結果數量，`Total: n.` 代表索引到n個結果。
> (OVR)全名為OVERRIDE，亦即被覆蓋，偵測到對應關鍵字時**並不會**使用該回覆組的回覆。
> (DEL)全名為DELETED，亦即已刪除，偵測到對應關鍵字時**並不會**使用該回覆組的回覆。
> (TOP)全名為TOP PAIR，亦即置頂指令，需要使用高權限指令才可以[新增](#m)或[刪除](#r)，此字組不會被一般自組覆蓋(OVERRIDE)，只會被同級字組覆蓋。
## I
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表要求顯示所有回覆組「水母」的詳細資訊。此語法一次可能顯示非常多字組(包含已覆蓋和使用中)。
```
JC  I  水母
```
**水母**為參數1(關鍵字)。
以下範例代表搜尋ID為87的關鍵字。此語法一次最多只會顯示一個字組。
```
JC  I  87  87
```
**87**同為參數1、參數2(ID)。
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

> Keyword 代表 關鍵字
> Reply 代表 回覆
> Override 代表 覆蓋，True為真(已覆蓋)；False為假(未覆蓋)
> Admin Pair 代表 高級字組，True為是；False為否
> Has been called n time(s). 代表 已經使用該字組回覆n次。當字組被覆蓋或刪除以後，便會停止計數。
> Created by 代表 由...製作
## K
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表顯示回覆次數前10名的關鍵字。
```
JC  K  10
```
**10**為參數1(名次)。
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
此功能沒有參數。
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
> Boot up Time 代表 開機時間，該時間為國際標準時間(UTC)，港澳台區使用者請自行+8小時(UTC+8)。
> Count of Keyword Pair 代表 目前資料庫總收錄字組數量
> Count of Reply 代表 目前已使用字組回覆的字次數
> Most Creative User 代表 目前製作最多關鍵字的使用者
> Most Popular Keyword 代表 目前回覆次數最多的字組
> Most Unpopular Keyword 代表 目前最冷門的字
> System command called time (including failed) 代表 目前已經呼叫系統指令的次數(包含呼叫失敗)
## H
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表獲取當前聊天頻道ID。
```
JC  H
```
這個指令沒有參數，
輸入後，如果沒有輸入錯誤、遺漏、頻道錯誤的話，將會顯示類似如下的回覆:
```
Type: User
```
```
Ud5a2b5bb5eca86342d3ed5e31d606e2c
```
> 為了[指令G](#g)使用方便，本指令抓取ID時特別使用兩則訊息發送。
## SHA
使用頻道

| C | R | G |
| :---: | :---: | :---: |
| ○ | ○ | ○ |

以下範例代表獲取**水母**的SHA-224加密字串。
```
JC  SHA  水母
```
**水母**為參數1(加密對象)
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

新增高階回覆組。於參數1輸入關鍵字，於參數2輸入回覆，參數3輸入密鑰。
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

建立關鍵字表格，無參數，平時不使用。
## G
(尚未完成))
