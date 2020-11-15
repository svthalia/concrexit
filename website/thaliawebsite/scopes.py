from oauth2_provider.scopes import SettingsScopes


class ApplicationSettingsScopes(SettingsScopes):
    """
    Backend for Django OAuth2 Toolkit that uses the settings scopes
    and limits the usage by applications based on the model
    """

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        scopes = super().get_available_scopes(application, request, *args, **kwargs)
        if application:
            scopes = [s for s in scopes if s in application.allowed_scopes]
        return scopes

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        scopes = super().get_default_scopes(application, request, *args, **kwargs)
        if application:
            scopes = [s for s in scopes if s in application.allowed_scopes]
        return scopes
