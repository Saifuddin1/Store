from app.models import SiteSettings
from app import db

def get_site_settings():
    settings = SiteSettings.query.first()

    if not settings:
        settings = SiteSettings(
            site_name="MyStore",
            logo_light="images/logo/logo.png",
            logo_dark="images/logo/logo-white.png"
        )
        db.session.add(settings)
        db.session.commit()

    return settings
