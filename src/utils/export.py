"""
Export Utilities
================
Functions for exporting data to CSV, Excel, and PDF formats.
"""

from datetime import date, datetime
from typing import Dict, List, Optional
import io
import pandas as pd


def export_to_csv(data: List[Dict], filename: str = "export.csv") -> bytes:
    """
    Export data to CSV format.
    
    Args:
        data: List of dictionaries to export
        filename: Suggested filename (not used, for reference)
    
    Returns:
        CSV file as bytes
    """
    if not data:
        return b""
    
    df = pd.DataFrame(data)
    
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    
    return buffer.getvalue().encode('utf-8')


def export_food_entries_csv(entries: List[Dict]) -> bytes:
    """
    Export food entries to CSV with formatted columns.
    
    Args:
        entries: List of food entry dictionaries
    
    Returns:
        CSV file as bytes
    """
    if not entries:
        return b"No data to export"
    
    # Prepare data with friendly column names
    export_data = []
    for entry in entries:
        export_data.append({
            "Date": entry.get("entry_date", ""),
            "Time": entry.get("entry_time", ""),
            "Meal Type": entry.get("dim_meal_type", {}).get("name", "Unknown") if isinstance(entry.get("dim_meal_type"), dict) else "",
            "Description": entry.get("food_description", ""),
            "Portion": entry.get("portion_description", ""),
            "Calories": entry.get("final_calories", 0),
            "Protein (g)": entry.get("final_protein_g", 0),
            "Carbs (g)": entry.get("final_carbs_g", 0),
            "Fat (g)": entry.get("final_fat_g", 0),
            "Manually Adjusted": "Yes" if entry.get("was_manually_adjusted") else "No",
            "Confidence": entry.get("llm_confidence_score", ""),
            "Notes": entry.get("notes", "")
        })
    
    return export_to_csv(export_data)


def export_daily_summaries_csv(summaries: List[Dict]) -> bytes:
    """
    Export daily summaries to CSV.
    
    Args:
        summaries: List of daily summary dictionaries
    
    Returns:
        CSV file as bytes
    """
    if not summaries:
        return b"No data to export"
    
    export_data = []
    for summary in summaries:
        export_data.append({
            "Date": summary.get("summary_date", ""),
            "Total Calories": summary.get("total_calories", 0),
            "Calorie Target": summary.get("calorie_target", 0),
            "Variance": summary.get("calorie_variance", 0),
            "Variance %": summary.get("calorie_variance_pct", 0),
            "Protein (g)": summary.get("total_protein_g", 0),
            "Carbs (g)": summary.get("total_carbs_g", 0),
            "Fat (g)": summary.get("total_fat_g", 0),
            "Total Entries": summary.get("total_entries", 0),
            "Has Breakfast": "Yes" if summary.get("has_breakfast") else "No",
            "Has Lunch": "Yes" if summary.get("has_lunch") else "No",
            "Has Dinner": "Yes" if summary.get("has_dinner") else "No",
            "Completeness": f"{(summary.get('logging_completeness_score', 0) or 0) * 100:.0f}%"
        })
    
    return export_to_csv(export_data)


def export_to_excel(
    entries: List[Dict], 
    summaries: List[Dict],
    user_profile: Dict,
    date_range: tuple
) -> bytes:
    """
    Export comprehensive data to Excel with multiple sheets.
    
    Args:
        entries: List of food entries
        summaries: List of daily summaries
        user_profile: User profile data
        date_range: Tuple of (start_date, end_date)
    
    Returns:
        Excel file as bytes
    """
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Summary sheet
        if user_profile:
            summary_info = {
                "Field": ["User", "Date Range", "Calorie Target", "Generated On"],
                "Value": [
                    user_profile.get("display_name", "User"),
                    f"{date_range[0]} to {date_range[1]}",
                    user_profile.get("daily_calorie_target", 2000),
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ]
            }
            pd.DataFrame(summary_info).to_excel(writer, sheet_name="Summary", index=False)
        
        # Daily Summaries sheet
        if summaries:
            summary_data = []
            for s in summaries:
                summary_data.append({
                    "Date": s.get("summary_date", ""),
                    "Calories": s.get("total_calories", 0),
                    "Target": s.get("calorie_target", 0),
                    "Variance": s.get("calorie_variance", 0),
                    "Protein (g)": s.get("total_protein_g", 0),
                    "Carbs (g)": s.get("total_carbs_g", 0),
                    "Fat (g)": s.get("total_fat_g", 0),
                    "Entries": s.get("total_entries", 0)
                })
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Daily Totals", index=False)
        
        # Food Entries sheet
        if entries:
            entry_data = []
            for e in entries:
                entry_data.append({
                    "Date": e.get("entry_date", ""),
                    "Time": e.get("entry_time", ""),
                    "Meal": e.get("dim_meal_type", {}).get("name", "") if isinstance(e.get("dim_meal_type"), dict) else "",
                    "Food": e.get("food_description", ""),
                    "Portion": e.get("portion_description", ""),
                    "Calories": e.get("final_calories", 0),
                    "Protein": e.get("final_protein_g", 0),
                    "Carbs": e.get("final_carbs_g", 0),
                    "Fat": e.get("final_fat_g", 0),
                    "Adjusted": "Yes" if e.get("was_manually_adjusted") else "No"
                })
            pd.DataFrame(entry_data).to_excel(writer, sheet_name="Food Log", index=False)
    
    return buffer.getvalue()


def generate_pdf_report(
    summaries: List[Dict],
    user_profile: Dict,
    date_range: tuple,
    stats: Dict
) -> bytes:
    """
    Generate a PDF report with charts and statistics.
    
    Args:
        summaries: List of daily summaries
        user_profile: User profile data
        date_range: Tuple of (start_date, end_date)
        stats: Calculated statistics
    
    Returns:
        PDF file as bytes
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return b"ReportLab not installed"
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("Calorie Tracking Report", title_style))
    elements.append(Paragraph(
        f"{date_range[0].strftime('%B %d, %Y')} - {date_range[1].strftime('%B %d, %Y')}",
        ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
    ))
    elements.append(Spacer(1, 20))
    
    # User Info
    if user_profile:
        elements.append(Paragraph("Profile Information", heading_style))
        user_data = [
            ["Name:", user_profile.get("display_name", "User")],
            ["Daily Calorie Target:", f"{user_profile.get('daily_calorie_target', 2000):,} cal"]
        ]
        user_table = Table(user_data, colWidths=[2*inch, 4*inch])
        user_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(user_table)
        elements.append(Spacer(1, 15))
    
    # Summary Statistics
    elements.append(Paragraph("Summary Statistics", heading_style))
    stats_data = [
        ["Days Tracked:", str(stats.get("days_tracked", 0))],
        ["Average Daily Calories:", f"{stats.get('avg_calories', 0):,.0f} cal"],
        ["Average vs Target:", f"{stats.get('avg_variance', 0):+,.0f} cal"],
        ["Days Under Target:", str(stats.get("days_under", 0))],
        ["Days Over Target:", str(stats.get("days_over", 0))],
        ["Total Protein:", f"{stats.get('total_protein', 0):,.0f}g"],
        ["Total Carbs:", f"{stats.get('total_carbs', 0):,.0f}g"],
        ["Total Fat:", f"{stats.get('total_fat', 0):,.0f}g"],
    ]
    stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Daily Breakdown Table
    if summaries:
        elements.append(Paragraph("Daily Breakdown", heading_style))
        
        table_data = [["Date", "Calories", "Target", "Variance", "Protein", "Carbs", "Fat"]]
        
        for s in summaries[-14:]:  # Last 14 days
            variance = s.get("calorie_variance", 0) or 0
            table_data.append([
                s.get("summary_date", ""),
                f"{s.get('total_calories', 0):,}",
                f"{s.get('calorie_target', 0):,}",
                f"{variance:+,}",
                f"{s.get('total_protein_g', 0) or 0:.0f}g",
                f"{s.get('total_carbs_g', 0) or 0:.0f}g",
                f"{s.get('total_fat_g', 0) or 0:.0f}g"
            ])
        
        daily_table = Table(table_data, colWidths=[1.1*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        daily_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        elements.append(daily_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"Generated by Calorie Vision Tracker on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    return buffer.getvalue()


def calculate_export_stats(summaries: List[Dict]) -> Dict:
    """Calculate statistics for export reports."""
    if not summaries:
        return {}
    
    total_calories = sum(s.get("total_calories", 0) or 0 for s in summaries)
    targets = [s.get("calorie_target", 0) or 0 for s in summaries]
    avg_target = sum(targets) / len(targets) if targets else 2000
    
    days_under = sum(1 for s in summaries if (s.get("total_calories", 0) or 0) < (s.get("calorie_target", 0) or 0))
    days_over = sum(1 for s in summaries if (s.get("total_calories", 0) or 0) > (s.get("calorie_target", 0) or 0))
    
    avg_calories = total_calories / len(summaries)
    
    return {
        "days_tracked": len(summaries),
        "total_calories": total_calories,
        "avg_calories": avg_calories,
        "avg_target": avg_target,
        "avg_variance": avg_calories - avg_target,
        "days_under": days_under,
        "days_over": days_over,
        "total_protein": sum(s.get("total_protein_g", 0) or 0 for s in summaries),
        "total_carbs": sum(s.get("total_carbs_g", 0) or 0 for s in summaries),
        "total_fat": sum(s.get("total_fat_g", 0) or 0 for s in summaries)
    }
