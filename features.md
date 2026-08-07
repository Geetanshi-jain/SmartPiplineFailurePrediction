# Smart Pipeline Failure Prediction - Key Features

This document provides a detailed overview of the core features of the Smart Pipeline Monitoring and Leakage Prediction System.

---

## 1. Dual Machine Learning Engine (Do-Tarfah AI System)
Is project mein ek nahi, balki **do alag-alag AI models (Random Forest)** ek sath kaam karte hain. Isiliye ise "Dual Engine" kaha gaya hai:
* **Pressure Regressor:** Yeh model pipe ke andar ke "dabav" (hydraulic pressure) ka anuman (prediction) lagata hai. Regression ka matlab hota hai kisi exact number ko predict karna (jaise 65.4 bar). Iska **R² score ~0.99** hai, jiska matlab hai ki iski prediction 99% tak accurate hai aur actual pressure ke bilkul kareeb hoti hai.
* **Leakage Classifier:** Classification ka matlab hota hai 'Haan' ya 'Na' mein jawab dena. Yeh model batata hai ki pipe leak ho rahi hai ya nahi. Real world mein leakages bohot kam hote hain (imbalanced data), fir bhi iska **ROC-AUC score ~0.99** hai. Iska matlab hai ki yeh model false alarms (galat warning) nahi deta aur asli leak ko bilkul sahi pakadta hai.

## 2. Interactive Bilingual Interface (English + Hindi)
Yeh ek bohot hi practical aur user-friendly feature hai. Bharat (India) jaise desh mein, ground-level operators ya jal-vibhag ke karmchari shayad English mein utne comfortable na hon.
* **Instant Toggle:** Isme ek button diya gaya hai jise click karte hi pura dashboard—graphs, charts, alerts, buttons aur yahan tak ki maps ke labels bhi—**turant Hindi se English ya English se Hindi** mein badal jate hain.
* Iske liye page ko refresh karne ki zaroorat nahi padti. Isse engineers aur ground staff dono ek hi system ko apni suvidha ke anusar use kar sakte hain.

## 3. Advanced GIS Network Map (Smart Naksha)
Yeh koi sadharan chart nahi hai, balki ek real-world geographical naksha (map) hai jo **Leaflet.js** technology par bana hai.
* **Satellite View:** Isme normal street map ke sath-sath **Esri Satellite imagery** ka support hai, yani aap bilkul waise hi buildings aur raste dekh sakte hain jaise Google Earth mein dikhte hain.
* **Color-Coded Risk Lines:** Nakshe par bichhi hui pipelines alag-alag rango (colors) mein chamakti hain:
  * 🟢 **Green (Safe):** Sab kuch normal chal raha hai.
  * 🟠 **Orange (Warning):** Pressure thoda upar-neeche hai, aage chalkar problem ho sakti hai (Maintenance ki zaroorat).
  * 🔴 **Red (Active Leak):** Yahan pipe phat gayi hai ya leak ho rahi hai, turant action lene ki zaroorat hai.

## 4. Internalized SMTP & Email Alarms (Automatic Alert System)
Agar system ko koi leak milta hai, toh sirf screen par red alert dikhana kaafi nahi hai. Pata chala operator screen nahi dekh raha!
* Isiliye isme **Gmail SMTP** ka inbuilt support diya gaya hai.
* Jaise hi 'Red Alert' trigger hota hai, system apne aap Nagar Nigam (Municipal authorities) ya on-duty engineer ko ek Email bhej deta hai.
* Iski UI (User Interface) itni simple banayi gayi hai ki kisko email bhejna hai, ye dashboard se hi asani se set aur change kiya ja sakta hai. Isse leak detect hone se lekar repair team ke nikalne tak ka response time bohot kam ho jata hai.

## 5. PDF Reports & Analytics Summary (Professional Reporting)
Officers aur management ko har roz ka data record karke rakhna hota hai. Ye system us kaam ko automatic kar deta hai.
* Ek click par system ek **Professional PDF Report** generate kar deta hai.
* Is report mein din bhar ke data ka summary, graphs (charts), kahan-kahan khatra hai uski list, aur 'Priority Maintenance' (yani sabse pehle kis pipe ko theek karna hai) ki puri detail hoti hai.
* Ye feature official meetings aur auditing ke liye bohot madadgaar hai.
