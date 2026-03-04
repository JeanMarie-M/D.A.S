import openpyxl
import csv
import io
from datetime import datetime
from .models import Student, Class, Dorm
from schools.models import School


def parse_date(value):
    """Try multiple date formats"""
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def import_students_from_xlsx(file, school):
    """
    Import students from an Excel (.xlsx) file.
    Returns a dict with success count, errors list, and skipped list.
    """
    result = {
        'success': 0,
        'updated': 0,
        'errors':  [],
        'skipped': [],
    }

    try:
        wb   = openpyxl.load_workbook(file)
        ws   = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        result['errors'].append(f"Could not read file: {e}")
        return result

    if not rows:
        result['errors'].append("File is empty.")
        return result

    # Skip header row
    headers = [str(h).strip().lower() if h else '' for h in rows[0]]
    data_rows = rows[1:]

    for i, row in enumerate(data_rows, start=2):
        row_num = f"Row {i}"

        # Skip completely empty rows
        if all(cell is None or str(cell).strip() == '' for cell in row):
            continue

        try:
            # Map columns
            def get(col_name):
                if col_name in headers:
                    val = row[headers.index(col_name)]
                    return str(val).strip() if val is not None else ''
                return ''

            admission_number = get('admission_number')
            first_name       = get('first_name')
            last_name        = get('last_name')
            class_name       = get('class')
            dorm_name        = get('dorm')
            date_str         = get('date_admitted')
            status           = get('status') or 'active'

            # Validate required fields
            if not admission_number:
                result['errors'].append(f"{row_num}: Missing admission number.")
                continue
            if not first_name or not last_name:
                result['errors'].append(f"{row_num}: Missing name for {admission_number}.")
                continue

            # Resolve class
            student_class = None
            if class_name:
                student_class = Class.objects.filter(
                    school=school,
                    form__name__icontains=class_name.replace(class_name[-1], '').strip(),
                    stream__iexact=class_name[-1]
                ).first()
                if not student_class:
                    result['errors'].append(
                        f"{row_num}: Class '{class_name}' not found for {admission_number}. Skipping class."
                    )

            # Resolve dorm
            student_dorm = None
            if dorm_name:
                student_dorm = Dorm.objects.filter(
                    school=school,
                    name__icontains=dorm_name
                ).first()
                if not student_dorm:
                    result['errors'].append(
                        f"{row_num}: Dorm '{dorm_name}' not found for {admission_number}. Skipping dorm."
                    )

            # Parse date
            date_admitted = parse_date(date_str) if date_str else None
            if not date_admitted:
                result['errors'].append(
                    f"{row_num}: Invalid date '{date_str}' for {admission_number}. Using today."
                )
                from django.utils import timezone
                date_admitted = timezone.now().date()

            # Validate status
            valid_statuses = ['active', 'prefect', 'medical', 'absent', 'inactive']
            if status not in valid_statuses:
                status = 'active'

            # Create or update student
            student, created = Student.objects.update_or_create(
                school=school,
                admission_number=admission_number,
                defaults={
                    'first_name':    first_name,
                    'last_name':     last_name,
                    'current_class': student_class,
                    'dorm':          student_dorm,
                    'date_admitted': date_admitted,
                    'status':        status,
                }
            )

            if created:
                result['success'] += 1
            else:
                result['updated'] += 1

        except Exception as e:
            result['errors'].append(f"{row_num}: Unexpected error — {e}")

    return result


def import_students_from_csv(file, school):
    """Import students from a CSV file."""
    result = {
        'success': 0,
        'updated': 0,
        'errors':  [],
        'skipped': [],
    }

    try:
        decoded = file.read().decode('utf-8')
        reader  = csv.DictReader(io.StringIO(decoded))
    except Exception as e:
        result['errors'].append(f"Could not read CSV: {e}")
        return result

    for i, row in enumerate(reader, start=2):
        try:
            admission_number = row.get('admission_number', '').strip()
            first_name       = row.get('first_name', '').strip()
            last_name        = row.get('last_name', '').strip()
            class_name       = row.get('class', '').strip()
            dorm_name        = row.get('dorm', '').strip()
            date_str         = row.get('date_admitted', '').strip()
            status           = row.get('status', 'active').strip()

            if not admission_number:
                result['errors'].append(f"Row {i}: Missing admission number.")
                continue

            student_class = Class.objects.filter(
                school=school,
                form__name__icontains=class_name[:-1].strip(),
                stream__iexact=class_name[-1]
            ).first() if class_name else None

            student_dorm = Dorm.objects.filter(
                school=school,
                name__icontains=dorm_name
            ).first() if dorm_name else None

            date_admitted = parse_date(date_str)
            if not date_admitted:
                from django.utils import timezone
                date_admitted = timezone.now().date()

            student, created = Student.objects.update_or_create(
                school=school,
                admission_number=admission_number,
                defaults={
                    'first_name':    first_name,
                    'last_name':     last_name,
                    'current_class': student_class,
                    'dorm':          student_dorm,
                    'date_admitted': date_admitted,
                    'status':        status or 'active',
                }
            )

            if created:
                result['success'] += 1
            else:
                result['updated'] += 1

        except Exception as e:
            result['errors'].append(f"Row {i}: {e}")

    return result