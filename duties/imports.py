import openpyxl
import csv
from .models import DutyArea
from students.models import Form, Dorm


def import_duties_from_xlsx(file, school):
    result = {'success': 0, 'updated': 0, 'errors': [], 'skipped': []}

    try:
        wb  = openpyxl.load_workbook(file)
        ws  = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        result['errors'].append(f"Could not read file: {e}")
        return result

    if not rows:
        result['errors'].append("File is empty.")
        return result

    # Normalize headers
    headers = [str(h).strip().lower().replace(' ', '_') if h else '' for h in rows[0]]

    required = ['label', 'name', 'students_required']
    for req in required:
        if req not in headers:
            result['errors'].append(f"Missing required column: '{req}'")
            return result

    for row_num, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue

        data = dict(zip(headers, row))

        try:
            label = str(data.get('label', '') or '').strip()
            name  = str(data.get('name',  '') or '').strip()

            if not label or not name:
                result['errors'].append(f"Row {row_num}: label and name are required.")
                continue

            # Area size
            area_size = str(data.get('area_size', 'medium') or 'medium').strip().lower()
            if area_size not in ['small', 'medium', 'large']:
                area_size = 'medium'

            # Is heavy
            is_heavy_raw = str(data.get('is_heavy', 'no') or 'no').strip().lower()
            is_heavy = is_heavy_raw in ['yes', 'true', '1']

            # Students required
            try:
                students_required = int(data.get('students_required', 1) or 1)
            except (ValueError, TypeError):
                students_required = 1

            # Specialization
            specialization = str(data.get('specialization', 'none') or 'none').strip().lower()
            if specialization not in ['none', 'form', 'dorm', 'class', 'subject']:
                specialization = 'none'

            # Tools
            tools_required = str(data.get('tools_required', '') or '').strip()

            # Specific form
            specific_form = None
            form_name = str(data.get('specific_form', '') or '').strip()
            if form_name and specialization == 'form':
                specific_form = Form.objects.filter(
                    school=school,
                    name__iexact=form_name
                ).first()
                if not specific_form:
                    result['errors'].append(
                        f"Row {row_num}: Form '{form_name}' not found."
                    )

            # Specific dorm
            specific_dorm = None
            dorm_name = str(data.get('specific_dorm', '') or '').strip()
            if dorm_name and specialization == 'dorm':
                specific_dorm = Dorm.objects.filter(
                    school=school,
                    name__iexact=dorm_name
                ).first()
                if not specific_dorm:
                    result['errors'].append(
                        f"Row {row_num}: Dorm '{dorm_name}' not found."
                    )

            # Create or update
            obj, created = DutyArea.objects.update_or_create(
                school=school,
                label=label,
                defaults={
                    'name':             name,
                    'area_size':        area_size,
                    'is_heavy':         is_heavy,
                    'students_required': students_required,
                    'specialization':   specialization,
                    'specific_form':    specific_form,
                    'specific_dorm':    specific_dorm,
                    'tools_required':   tools_required,
                    'is_active':        True,
                }
            )

            if created:
                result['success'] += 1
            else:
                result['updated'] += 1

        except Exception as e:
            result['errors'].append(f"Row {row_num}: {e}")

    return result


def import_duties_from_csv(file, school):
    result = {'success': 0, 'updated': 0, 'errors': [], 'skipped': []}

    try:
        decoded = file.read().decode('utf-8')
        reader  = csv.DictReader(decoded.splitlines())
    except Exception as e:
        result['errors'].append(f"Could not read file: {e}")
        return result

    for row_num, row in enumerate(reader, start=2):
        try:
            label = str(row.get('label', '') or '').strip()
            name  = str(row.get('name',  '') or '').strip()

            if not label or not name:
                result['errors'].append(f"Row {row_num}: label and name required.")
                continue

            area_size = str(row.get('area_size', 'medium') or 'medium').strip().lower()
            if area_size not in ['small', 'medium', 'large']:
                area_size = 'medium'

            is_heavy_raw = str(row.get('is_heavy', 'no') or 'no').strip().lower()
            is_heavy = is_heavy_raw in ['yes', 'true', '1']

            try:
                students_required = int(row.get('students_required', 1) or 1)
            except (ValueError, TypeError):
                students_required = 1

            specialization = str(row.get('specialization', 'none') or 'none').strip().lower()
            if specialization not in ['none', 'form', 'dorm', 'class', 'subject']:
                specialization = 'none'

            tools_required = str(row.get('tools_required', '') or '').strip()

            specific_form = None
            form_name = str(row.get('specific_form', '') or '').strip()
            if form_name and specialization == 'form':
                specific_form = Form.objects.filter(
                    school=school, name__iexact=form_name
                ).first()

            specific_dorm = None
            dorm_name = str(row.get('specific_dorm', '') or '').strip()
            if dorm_name and specialization == 'dorm':
                specific_dorm = Dorm.objects.filter(
                    school=school, name__iexact=dorm_name
                ).first()

            obj, created = DutyArea.objects.update_or_create(
                school=school,
                label=label,
                defaults={
                    'name':             name,
                    'area_size':        area_size,
                    'is_heavy':         is_heavy,
                    'students_required': students_required,
                    'specialization':   specialization,
                    'specific_form':    specific_form,
                    'specific_dorm':    specific_dorm,
                    'tools_required':   tools_required,
                    'is_active':        True,
                }
            )

            if created:
                result['success'] += 1
            else:
                result['updated'] += 1

        except Exception as e:
            result['errors'].append(f"Row {row_num}: {e}")

    return result