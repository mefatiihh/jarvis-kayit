#!/usr/bin/env python3
"""
Apple Health Data Parser & Daily Reporter
Reads Health Auto Export CSV files
Generates daily health reports for Telegram delivery
"""

import csv
import json
import os
import sys
import glob
from datetime import datetime, date, timedelta
from pathlib import Path

# --- Configuration ---
CONFIG_PATH = Path(__file__).parent / "health-config.json"

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

# --- Data Sources ---

def find_export_dir():
    """Find the latest Health Auto Export directory"""
    config = load_config()
    
    if "data_path" in config and config["data_path"]:
        path = Path(config["data_path"])
        if path.exists():
            return path
    
    # Check Downloads for HealthAutoExport folders
    dl_dir = Path.home() / "Downloads"
    export_dirs = sorted(dl_dir.glob("HealthAutoExport_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if export_dirs:
        return export_dirs[0]
    
    return None


# --- CSV Parsing ---

# Column mapping: Turkish column name -> our internal key
COLUMN_MAP = {
    "Adım Sayısı (count)": ("steps", "count"),
    "Yürüme + Koşma Mesafesi (km)": ("distance", "km"),
    "Aktif Enerji (kJ)": ("active_energy_kj", "kJ"),
    "Dinlenme Enerjisi (kJ)": ("resting_energy_kj", "kJ"),
    "Apple Egzersiz Süresi (min)": ("exercise_minutes", "min"),
    "Apple Ayakta Durma Süresi (min)": ("stand_minutes", "min"),
    "Kalp Hızı [Ort] (count/min)": ("heart_rate_avg", "bpm"),
    "Kalp Hızı [Maks] (count/min)": ("heart_rate_max", "bpm"),
    "Kalp Hızı [Dakika] (count/min)": ("heart_rate_min", "bpm"),
    "Kalp Hızı Değişkenliği (ms)": ("hrv", "ms"),
    "Dinlenme Kalp Hızı (count/min)": ("resting_heart_rate", "bpm"),
    "Ağırlık (kg)": ("weight", "kg"),
    "Vücut Yağ Oranı (%)": ("body_fat", "%"),
    "Vücut Kitle İndeksi (count)": ("bmi", "count"),
    "Vücut Sıcaklığı (degC)": ("body_temp", "°C"),
    "Bazal Vücut Sıcaklığı (degC)": ("basal_temp", "°C"),
    "Çıkılan Katlar (count)": ("flights_climbed", "count"),
    "Diyetik Enerji (kJ)": ("dietary_energy_kj", "kJ"),
    "Protein (g)": ("protein", "g"),
    "Karbonhidratlar (g)": ("carbs", "g"),
    "Toplam Yağ (g)": ("fat", "g"),
    "Su (mL)": ("water", "mL"),
    "Uyku Analizi [Total] (hr)": ("sleep_total", "hr"),
    "Uyku Analizi [Uykuda] (hr)": ("sleep_asleep", "hr"),
    "Uyku Analizi [Derin] (hr)": ("sleep_deep", "hr"),
    "Uyku Analizi [REM] (hr)": ("sleep_rem", "hr"),
    "VO2 Max (ml/(kg·min))": ("vo2max", "ml/(kg·min)"),
    "Yağsız Vücut Ağırlığı (kg)": ("lean_body_mass", "kg"),
    "Kafein (mg)": ("caffeine", "mg"),
    "Kolesterol (mg)": ("cholesterol", "mg"),
    "Sodyum (mg)": ("sodium", "mg"),
    "Lif (g)": ("fiber", "g"),
    "Şeker (g)": ("sugar", "g"),
    "Doymuş Yağ (g)": ("saturated_fat", "g"),
    "Yürüme Hızı (km/hr)": ("walking_speed", "km/h"),
    "Yürüyüş Kalp Atış Hızı Ortalaması (count/min)": ("walking_hr_avg", "bpm"),
    "Bisiklet Mesafesi (km)": ("cycling_distance", "km"),
    "Uyku Analizi [Yatakta] (hr)": ("sleep_in_bed", "hr"),
}

# Column groups for report sections
COLUMN_GROUPS = {
    "🏃 Aktivite": {
        "steps": "👣 Adım",
        "distance": "📏 Mesafe",
        "active_energy_kj": "🔥 Aktif Kalori",
        "exercise_minutes": "⏱️ Egzersiz",
        "stand_minutes": "🧍 Ayakta",
        "flights_climbed": "🏢 Kat",
        "cycling_distance": "🚴 Bisiklet",
        "walking_speed": "🚶 Yürüme Hızı",
    },
    "❤️ Nabız": {
        "heart_rate_avg": "   Ort",
        "heart_rate_min": "   Min",
        "heart_rate_max": "   Max",
        "resting_heart_rate": "   Dinlenme",
        "walking_hr_avg": "   Yürüme Ort",
        "hrv": "   HRV",
    },
    "🥗 Beslenme": {
        "dietary_energy_kj": "🥗 Kalori",
        "protein": "🥩 Protein",
        "carbs": "🍚 Karbonhidrat",
        "fat": "🧈 Yağ",
        "saturated_fat": "   Doymuş Yağ",
        "fiber": "🌾 Lif",
        "sugar": "🍬 Şeker",
        "water": "💧 Su",
        "caffeine": "☕ Kafein",
        "sodium": "🧂 Sodyum",
        "cholesterol": "🫀 Kolesterol",
    },
    "😴 Uyku": {
        "sleep_total": "   Toplam",
        "sleep_asleep": "   Uykuda",
        "sleep_deep": "   Derin",
        "sleep_rem": "   REM",
        "sleep_in_bed": "   Yatakta",
    },
    "⚖️ Vücut": {
        "weight": "⚖️ Kilo",
        "body_fat": "💪 Vücut Yağı",
        "lean_body_mass": "   Yağsız Kütle",
        "bmi": "📐 BMI",
        "body_temp": "🌡️ Vücut Sıcaklığı",
        "vo2max": "🏃 VO2 Max",
    },
}

def parse_csv(data_dir, target_dates):
    """Parse Health Auto Export CSV files and return data for requested dates"""
    csv_file = None
    
    # Find the main health export CSV
    for f in data_dir.glob("HealthAutoExport-*.csv"):
        # Don't use empty files
        if f.stat().st_size > 0:
            csv_file = f
            break
    
    if not csv_file:
        print(f"⚠️  Ana CSV dosyası bulunamadı.", file=sys.stderr)
        return {}
    
    print(f"📄 CSV okunuyor: {csv_file.name}", file=sys.stderr)
    
    # Build reverse column map (Column name -> (key, unit))
    column_keys = {}
    for col_name, (key, unit) in COLUMN_MAP.items():
        column_keys[col_name] = (key, unit)
    
    daily_data = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            date_str = row.get('Tarih/Saat', '')
            if not date_str:
                continue
            
            # Extract YYYY-MM-DD from "2026-02-11 00:00:00"
            day = date_str[:10]
            
            if day not in target_dates:
                continue
            
            entry = {}
            
            for col_name, value_str in row.items():
                if col_name not in column_keys:
                    continue
                
                key, unit = column_keys[col_name]
                
                # Skip empty values
                if not value_str or value_str.strip() == '':
                    continue
                
                try:
                    value = float(value_str)
                    entry[key] = {"value": value, "unit": unit}
                except ValueError:
                    continue
            
            if entry:
                daily_data[day] = entry
    
    return daily_data


def parse_workouts(data_dir):
    """Parse workout CSV for additional exercise details"""
    workout_file = None
    for f in data_dir.glob("Workouts-*.csv"):
        if f.stat().st_size > 0:
            workout_file = f
            break
    
    if not workout_file:
        return []
    
    workouts = []
    with open(workout_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            workouts.append(row)
    
    return workouts


# --- Unit Conversions ---

def kj_to_kcal(kj):
    """Convert kilojoules to kilocalories"""
    return kj * 0.239006


def format_value(key, entry):
    """Format a metric value nicely"""
    if not entry:
        return None
    
    value = entry["value"]
    unit = entry.get("unit", "")
    
    # Special formatting
    if key == "steps":
        return f'{value:,.0f}'
    elif key in ("distance", "cycling_distance"):
        return f'{value:.2f} km'
    elif key in ("active_energy_kj", "resting_energy_kj", "dietary_energy_kj"):
        kcal = kj_to_kcal(value)
        return f'{kcal:,.0f} kcal ({value:,.0f} kJ)'
    elif key == "water":
        if value >= 1000:
            return f'{value/1000:.2f} L ({value:,.0f} mL)'
        return f'{value:,.0f} mL'
    elif key == "sleep_total":
        hrs = int(value)
        mins = int((value - hrs) * 60)
        if mins > 0:
            return f'{hrs}s {mins}dk'
        return f'{hrs}s'
    elif key in ("sleep_asleep", "sleep_deep", "sleep_rem", "sleep_in_bed"):
        hrs = int(value)
        mins = int((value - hrs) * 60)
        return f'{hrs}s {mins}dk'
    elif key in ("heart_rate_avg", "heart_rate_min", "heart_rate_max", "resting_heart_rate", "walking_hr_avg"):
        return f'{value:.0f} bpm'
    elif key == "hrv":
        return f'{value:.0f} ms'
    elif key == "weight":
        return f'{value:.1f} kg'
    elif key == "body_fat":
        return f'{value:.1f}%'
    elif key == "bmi":
        return f'{value:.1f}'
    elif key in ("body_temp", "basal_temp"):
        return f'{value:.1f}°C'
    elif key in ("vo2max"):
        return f'{value:.1f} ml/kg/dk'
    elif key in ("protein", "carbs", "fat", "fiber", "sugar", "saturated_fat"):
        return f'{value:.0f}g'
    elif key == "sodium":
        return f'{value:.0f}mg'
    elif key == "caffeine":
        return f'{value:.0f}mg'
    elif key == "cholesterol":
        return f'{value:.0f}mg'
    elif key == "walking_speed":
        return f'{value:.2f} km/s'
    elif key == "flights_climbed":
        return f'{value:.0f}'
    elif key in ("exercise_minutes", "stand_minutes"):
        return f'{value:.0f} dk'
    elif key == "lean_body_mass":
        return f'{value:.1f} kg'
    else:
        return f'{value} {unit}'.strip()


# --- Report Generation ---

def get_compact_value(entry, key, short_format=True):
    """Get a compact value for summary display"""
    if not entry:
        return None
    
    value = entry["value"]
    
    if key in ("active_energy_kj", "dietary_energy_kj"):
        kcal = kj_to_kcal(value)
        return f'{kcal:,.0f}'
    elif key == "distance":
        return f'{value:.2f}'
    elif key == "exercise_minutes":
        return f'{value:.0f}'
    elif key == "steps":
        return f'{value:,.0f}'
    elif key == "water":
        if short_format:
            return f'{value/1000:.1f}L'
        return f'{value:,.0f}'
    elif key in ("weight",):
        return f'{value:.1f}'
    elif key in ("heart_rate_avg", "resting_heart_rate"):
        return f'{value:.0f}'
    elif key in ("sleep_total",):
        return f'{value:.1f}'
    
    return None


def generate_daily_report(daily_data, target_date=None, include_workouts=None):
    """Generate a formatted daily health report"""
    if target_date is None:
        target_date = date.today().isoformat()
    
    if target_date not in daily_data or not daily_data[target_date]:
        return None
    
    day_data = daily_data[target_date]
    lines = []
    
    # Date header
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    month_names = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    lines.append(f"📊 {dt.day} {month_names[dt.month-1]} {dt.year} {day_names[dt.weekday()]}")
    lines.append("─" * 28)
    
    # Workout summary
    if include_workouts:
        today_workouts = []
        for w in include_workouts:
            w_date = w.get('Start', '')[:10]
            if w_date == target_date:
                today_workouts.append(w)
        
        if today_workouts:
            lines.append("")
            lines.append(f"🏋️ **Antrenman ({len(today_workouts)} adet)**")
            for w in today_workouts:
                w_name = w.get('Workout Type', 'Egzersiz')
                w_dur_str = w.get('Duration', '')
                w_cal = w.get('Aktif Enerji (kJ)', '')
                w_dist = w.get('Mesafe (km)', '')
                w_hr = w.get('Ort. Kalp Hızı (count/min)', '')
                w_hr_max = w.get('Maks. Kalp Atış Hızı (count/min)', '')
                
                # Parse duration (HH:MM:SS)
                dur_min = ''
                if w_dur_str and ':' in w_dur_str:
                    parts_time = w_dur_str.split(':')
                    if len(parts_time) == 3:
                        h, m, s = parts_time
                        dur_min = f'{int(h)*60 + int(m) + int(s)//60}'
                
                parts = [f"   {w_name}"]
                if dur_min:
                    parts.append(f"⏱️ {dur_min}dk")
                if w_cal and w_cal.strip():
                    parts.append(f"🔥 {kj_to_kcal(float(w_cal)):.0f}kcal")
                if w_dist and w_dist.strip():
                    parts.append(f"📏 {float(w_dist):.2f}km")
                if w_hr and w_hr.strip():
                    parts.append(f"❤️ {float(w_hr):.0f}bpm")
                if w_hr_max and w_hr_max.strip():
                    parts.append(f"⬆️ {float(w_hr_max):.0f}bpm")
                lines.append(" | ".join(parts))
    
    # Generate sections
    for group_name, metrics in COLUMN_GROUPS.items():
        section_lines = []
        for key, display_name in metrics.items():
            if key in day_data:
                formatted = format_value(key, day_data[key])
                if formatted:
                    section_lines.append(f"{display_name}: {formatted}")
        
        if section_lines:
            lines.append("")
            lines.append(f"**{group_name}**")
            lines.extend(section_lines)
    
    # Tips/goals
    config = load_config()
    step_goal = config.get("daily_step_goal", 10000)
    cal_goal = config.get("daily_calorie_budget", None)
    
    tips = []
    if "steps" in day_data:
        steps = day_data["steps"]["value"]
        if steps >= step_goal:
            tips.append(f"✅ Adım hedefi: {steps:,.0f} / {step_goal:,} — HEDEFE ULAŞTIN 🎯")
        else:
            pct = (steps / step_goal) * 100
            remaining = step_goal - steps
            tips.append(f"📊 Adım: {steps:,.0f} / {step_goal:,} (%{pct:.0f}) — Kalan {remaining:,}")
    
    if "active_energy_kj" in day_data and cal_goal:
        active_kcal = kj_to_kcal(day_data["active_energy_kj"]["value"])
        if active_kcal >= cal_goal:
            tips.append(f"🔥 Kalori hedefi: {active_kcal:,.0f} / {cal_goal:,} kcal — HEDEFE ULAŞTIN")
    
    if "water" in day_data:
        water_l = day_data["water"]["value"] / 1000
        if water_l >= 2.0:
            tips.append(f"💧 Su: {water_l:.1f}L — İyi seviye ✅")
        else:
            tips.append(f"💧 Su: {water_l:.1f}L — Hedef 2L")
    
    if tips:
        lines.append("")
        lines.extend(tips)
    
    return "\n".join(lines)


def generate_compact_summary(daily_data, target_date=None):
    """Generate a one-line compact summary"""
    if target_date is None:
        target_date = date.today().isoformat()
    
    if target_date not in daily_data or not daily_data[target_date]:
        return "⚠️ Veri yok"
    
    day_data = daily_data[target_date]
    parts = []
    
    steps = day_data.get("steps", {}).get("value", 0)
    distance = day_data.get("distance", {}).get("value", 0)
    active_kj = day_data.get("active_energy_kj", {}).get("value", 0)
    exercise = day_data.get("exercise_minutes", {}).get("value", 0)
    hr_avg = day_data.get("heart_rate_avg", {}).get("value", 0)
    sleep = day_data.get("sleep_total", {}).get("value", 0)
    protein = day_data.get("protein", {}).get("value", 0)
    
    if steps:
        parts.append(f"👣 {steps:,.0f}")
    if exercise:
        parts.append(f"⏱️ {exercise:.0f}dk")
    if distance:
        parts.append(f"📏 {distance:.2f}km")
    if active_kj:
        kcal = kj_to_kcal(active_kj)
        parts.append(f"🔥 {kcal:,.0f}")
    if hr_avg:
        parts.append(f"❤️ {hr_avg:.0f}")
    if sleep:
        parts.append(f"😴 {sleep:.1f}s")
    
    return " | ".join(parts) if parts else "⚠️ Veri yok"


def generate_weekly_report(daily_data, end_date=None):
    """Generate weekly summary"""
    if end_date is None:
        end_date = date.today()
    
    start_date = end_date - timedelta(days=6)
    
    month_names = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    lines = []
    lines.append(f"📊 **Haftalık Sağlık Özeti**")
    lines.append(f"   {start_date.day} {month_names[start_date.month-1]} — {end_date.day} {month_names[end_date.month-1]} {end_date.year}")
    lines.append("─" * 28)
    
    # Aggregate
    totals = {}
    daily_steps = []
    day_count = 0
    best_day = None
    
    current = start_date
    while current <= end_date:
        ds = current.isoformat()
        if ds in daily_data and daily_data[ds]:
            day_count += 1
            for key, entry in daily_data[ds].items():
                if key not in totals:
                    totals[key] = 0
                totals[key] += entry["value"]
            
            if "steps" in daily_data[ds]:
                s = daily_data[ds]["steps"]["value"]
                daily_steps.append((ds, s))
                if best_day is None or s > best_day[1]:
                    best_day = (ds, s)
        current += timedelta(days=1)
    
    if day_count == 0:
        return None
    
    lines.append("")
    lines.append(f"📅 {day_count}/7 gün veri var")
    
    if "steps" in totals:
        avg = totals["steps"] / day_count
        lines.append(f"👣 **Toplam Adım:** {totals['steps']:,.0f}")
        lines.append(f"   Günlük Ort: {avg:,.0f}")
        if best_day:
            lines.append(f"   En İyi Gün: {best_day[0]} ({best_day[1]:,} adım)")
    
    if "active_energy_kj" in totals:
        kcal = kj_to_kcal(totals["active_energy_kj"])
        lines.append(f"🔥 **Toplam Aktif Kalori:** {kcal:,.0f} kcal")
    
    if "exercise_minutes" in totals:
        total_min = totals["exercise_minutes"]
        lines.append(f"⏱️  **Toplam Egzersiz:** {total_min:.0f} dk ({total_min/60:.1f} saat)")
    
    if "distance" in totals:
        lines.append(f"📏 **Toplam Mesafe:** {totals['distance']:.2f} km")
    
    if "sleep_total" in totals:
        avg_sleep = totals["sleep_total"] / day_count
        lines.append(f"😴 **Ortalama Uyku:** {avg_sleep:.1f} saat")
    
    if "protein" in totals:
        avg_protein = totals["protein"] / day_count
        lines.append(f"🥩 **Ortalama Protein:** {avg_protein:.0f}g/gün")
    
    if "water" in totals:
        avg_water = totals["water"] / day_count / 1000
        lines.append(f"💧 **Ortalama Su:** {avg_water:.1f}L/gün")
    
    return "\n".join(lines)


# --- Main ---

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    mode = sys.argv[2] if len(sys.argv) > 2 else "daily"
    
    print(f"🔍 Sağlık verileri taranıyor...", file=sys.stderr)
    
    data_dir = find_export_dir()
    if not data_dir:
        print("❌ Health Auto Export klasörü bulunamadı.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Çözüm: iPhone → Health Auto Export uygulamasından export al", file=sys.stderr)
        print("       veya Downloads klasörüne 'HealthAutoExport_...' klasörünü at.", file=sys.stderr)
        sys.exit(1)
    
    print(f"📁 Klasör: {data_dir.name}", file=sys.stderr)
    
    # Parse today and yesterday for daily, last 7 days for weekly
    today = date.today()
    yesterday = today - timedelta(days=1)
    target_dates = set()
    
    if mode == "daily":
        target_dates.add(target_date)
    elif mode == "weekly":
        for i in range(7):
            d = today - timedelta(days=i)
            target_dates.add(d.isoformat())
    elif mode == "compact":
        target_dates.add(target_date)
    elif mode == "all":
        # Get all available dates by scanning the CSV
        pass  # handled below
    
    daily_data = parse_csv(data_dir, target_dates)
    workouts = parse_workouts(data_dir)
    
    if not daily_data:
        print("❌ İstenen tarih için veri bulunamadı.", file=sys.stderr)
        sys.exit(1)
    
    if mode == "daily":
        report = generate_daily_report(daily_data, target_date, workouts)
        if report:
            print(report)
        else:
            print(f"⚠️ {target_date} için veri yok.")
    
    elif mode == "weekly":
        report = generate_weekly_report(daily_data)
        if report:
            print(report)
        else:
            print("⚠️ Haftalık rapor oluşturulamadı.")
    
    elif mode == "compact":
        summary = generate_compact_summary(daily_data, target_date)
        print(summary)
    
    elif mode == "all":
        print("📅 **Tüm Mevcut Veriler**")
        for dt in sorted(daily_data.keys()):
            summary = generate_compact_summary(daily_data, dt)
            day_data = daily_data[dt]
            weight = day_data.get("weight", {})
            w_str = f" ⚖️ {weight['value']:.1f}kg" if weight else ""
            print(f"   {dt}: {summary}{w_str}")
    
    else:
        print(f"❌ Bilinmeyen mod: {mode}")
        print("Kullanım: python3 health-parser.py [YYYY-AA-GG] [daily|weekly|compact|all]")


if __name__ == "__main__":
    main()
