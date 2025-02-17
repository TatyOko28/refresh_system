class EmailHunterService:
    @staticmethod
    async def verify_email(email):
        # Pour les besoins des tests, on retourne toujours un résultat valide.
        return {'is_valid': True}
