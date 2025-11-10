from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Department, Role, StaffProfile


class Command(BaseCommand):
    help = "Seed demo data for GHMS (departments, roles, demo staff users)."

    def handle(self, *args, **options):
        # 1. Departments
        departments = [
            ("OPD", "Outpatient Department"),
            ("LAB", "Laboratory"),
            ("PHARM", "Pharmacy"),
            ("RAD", "Radiology"),
            ("FIN", "Finance / Billing"),
            ("REC", "Reception / Registration"),
            ("WARD", "Inpatient Ward"),
            ("ADMIN", "Administration"),
        ]

        for code, name in departments:
            Department.objects.get_or_create(code=code, defaults={"name": name})
        self.stdout.write(self.style.SUCCESS("Departments seeded."))

        # 2. Roles (aligned with StaffProfile ROLE_CHOICES)
        roles = [
            ("OPD_DOCTOR", "OPD Doctor"),
            ("NURSE", "Nurse"),
            ("PHARMACIST", "Pharmacist"),
            ("LAB_TECH", "Lab Technician"),
            ("RADIOLOGY", "Radiology Staff"),
            ("FINANCE", "Finance Officer"),
            ("RECEPTION", "Reception / Registration"),
            ("ADMIN", "System Admin"),
            ("AUDITOR", "Auditor"),
        ]

        for rc, rn in roles:
            Role.objects.get_or_create(code=rc, defaults={"name": rn})
        self.stdout.write(self.style.SUCCESS("Roles seeded."))

        # Simple helper to get dep + role
        def get_dep(code):
            return Department.objects.get(code=code)

        def get_role(code):
            return Role.objects.get(code=code)

        # 3. Demo users + StaffProfiles
        demo_users = [
            ("admin", "ADMIN", "ADMIN"),
            ("auditor", "ADMIN", "AUDITOR"),
            ("opd_doc", "OPD", "OPD_DOCTOR"),
            ("nurse1", "WARD", "NURSE"),
            ("pharm1", "PHARM", "PHARMACIST"),
            ("lab1", "LAB", "LAB_TECH"),
            ("fin1", "FIN", "FINANCE"),
            ("rec1", "REC", "RECEPTION"),
        ]

        for username, dep_code, role_code in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"is_staff": True},
            )
            if created:
                user.set_password("Pass1234!")
                # make admin user superuser
                if username == "admin":
                    user.is_superuser = True
                user.save()

            StaffProfile.objects.get_or_create(
                user=user,
                defaults={
                    "department": get_dep(dep_code),
                    "role": role_code,
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo users & staff profiles seeded."))

        self.stdout.write(self.style.SUCCESS("GHMS demo seed complete."))
