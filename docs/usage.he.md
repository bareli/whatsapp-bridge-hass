# שימוש

## הגדרות חיבור

| אפשרות | ברירת מחדל | תיאור |
|---|---|---|
| Host | `core-whatsapp_bridge` | כתובת המארח של התוסף. |
| Port | `8080` | הפורט של התוסף. |
| API token | ריק | מאוחזר מהתוסף כשהשדה נשאר ריק. |

אם התוסף דוחה את האסימון בהמשך, Home Assistant פותח תהליך אימות מחדש שבו מזינים אסימון חדש.

## יעדים

כל שירות שמקבל `target` (או `recipient`) מקבל אחד מאלה:

- מספר טלפון, למשל `+972501234567`. תווים שאינם ספרות או `+` מוסרים, ו-`+` חסר בתחילת
  המספר מתווסף;
- שם איש קשר מפנקס הכתובות (ללא הבחנה בין אותיות גדולות לקטנות);
- מזהה (id) של איש קשר מפנקס הכתובות.

## שירותים

### `whatsapp_bridge.send_text`

| שדה | חובה | תיאור |
|---|---|---|
| `target` | כן | טלפון, שם איש קשר או מזהה איש קשר. |
| `message` | כן | גוף ההודעה. |
| `quoted_msg_id` | לא | מזהה של הודעה לציטוט. |

### `whatsapp_bridge.send_media`

| שדה | חובה | תיאור |
|---|---|---|
| `target` | כן | טלפון, שם איש קשר או מזהה איש קשר. |
| `caption` | לא | כיתוב. |
| `media_url` | אחד מהשניים | כתובת HTTPS להורדה ושליחה. |
| `media_path` | אחד מהשניים | נתיב קובץ מקומי בתוך תיקיית התצורה של HA (חייב להיות נתיב מותר). |
| `as_document` | לא | שליחה כמסמך. ברירת מחדל: `false`. |
| `as_voice` | לא | שליחה כהודעה קולית. ברירת מחדל: `false`. |

אי אפשר לציין גם `media_url` וגם `media_path`.

### `whatsapp_bridge.send_location`

| שדה | חובה | תיאור |
|---|---|---|
| `recipient` | כן | טלפון, שם איש קשר או מזהה איש קשר. |
| `latitude` | כן | בין `-90` ל-`90`. |
| `longitude` | כן | בין `-180` ל-`180`. |
| `name` | לא | שם המקום. |

### שירותי פנקס הכתובות

| שירות | שדות |
|---|---|
| `whatsapp_bridge.contact_add` | `name` ו-`phone` (חובה), `tags`, `notes` |
| `whatsapp_bridge.contact_update` | `contact_id` (חובה), `name`, `phone`, `tags`, `notes` |
| `whatsapp_bridge.contact_delete` | `contact_id` (חובה) |

פנקס הכתובות נשמר ב-`<config>/.storage/whatsapp_bridge.contacts` ונכלל בגיבויים של
Home Assistant.

### שירותי הסשן

| שירות | מה הוא עושה |
|---|---|
| `whatsapp_bridge.session_logout` | מכריח צימוד מחדש עם הטלפון; בהפעלה הבאה יוצג קוד QR חדש. |
| `whatsapp_bridge.session_restart` | יוצר מחדש את לקוח WhatsApp Web בלי לאבד את הסשן. |

## `notify.whatsapp`

קוראים לו עם `target` (מחרוזת או רשימה) ו-`message`. בלוק `data` האופציונלי מקבל
`media_url`, `media_path`, `caption`, `as_document` ו-`as_voice`. בלי `media_*` ההודעה
נשלחת כטקסט. קריאה בלי יעד מתעלמת ממנה עם אזהרה ביומן, ומספר טלפון לא תקין מדולג עם אזהרה.

## ישויות

| ישות | הערות |
|---|---|
| חיישן מצב | Enum: Initialising, Waiting for QR scan, Loading, Ready, Disconnected. מאפיינים: `phone`, `push_name`, `last_seen_at`. |
| חיישן סוללת הטלפון | אחוזים. |
| חיישן Last message at | חותמת זמן. |
| חיישן בינארי Connected | מחלקת קישוריות. |
| תמונת QR code | PNG של קוד הצימוד. |

כל הישויות שייכות להתקן אחד בשם **WhatsApp Bridge**. בהתקנות חדשות מזהי הישויות מתחילים
בקידומת `whatsapp_bridge_` (למשל `sensor.whatsapp_bridge_state` ו-`image.whatsapp_bridge_qr`);
התקנות שנעשו לפני 0.1.5 שומרות על המזהים הישנים. את המזהים המדויקים אצלכם תמצאו תחת
**הגדרות ← מכשירים ושירותים ← WhatsApp Bridge**.

## פאנל הצד

בפאנל **WhatsApp** שלוש לשוניות:

- **Contacts**: רשימה, הוספה, עריכה ומחיקה של אנשי קשר, ושליחת הודעת טקסט לאיש קשר.
- **Conversations**: היסטוריית שיחות עדיין לא נשמרת מקומית; הלשונית מפנה לאירוע
  `whatsapp_message_received`.
- **Settings**: הפעלה מחדש של הלקוח, או התנתקות שמכריחה צימוד מחדש.
