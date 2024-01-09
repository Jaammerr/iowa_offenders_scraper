from loguru import logger
from tortoise import fields, Model


class OffendersData(Model):
    registration_number = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=True)
    gender = fields.CharField(max_length=255, null=True)
    race = fields.CharField(max_length=255, null=True)
    birthdate = fields.CharField(max_length=255, null=True)
    height = fields.CharField(max_length=255, null=True)
    weight = fields.CharField(max_length=255, null=True)
    hair_color = fields.CharField(max_length=255, null=True)
    eye_color = fields.CharField(max_length=255, null=True)
    scars = fields.CharField(max_length=2000, null=True)
    address = fields.CharField(max_length=2000, null=True)
    tier = fields.CharField(max_length=255, null=True)
    residency = fields.CharField(max_length=255, null=True)
    exclusion = fields.CharField(max_length=255, null=True)
    employment = fields.CharField(max_length=255, null=True)


    @classmethod
    async def add_offender(
            cls,
            registration_number: int,
            name: str = None,
            gender: str = None,
            race: str = None,
            birthdate: str = None,
            height: str = None,
            weight: str = None,
            hair_color: str = None,
            eye_color: str = None,
            scars: str = None,
            address: str = None,
            tier: str = None,
            residency: str = None,
            exclusion: str = None,
            employment: str = None,
    ) -> bool:
        try:

            if await cls.is_offender_exists(registration_number):
                logger.warning(f"Offender with registration number {registration_number} already exists")
                return True

            await cls.create(
                registration_number=registration_number,
                name=name,
                gender=gender,
                race=race,
                birthdate=birthdate,
                height=height,
                weight=weight,
                hair_color=hair_color,
                eye_color=eye_color,
                scars=scars,
                address=address,
                tier=tier,
                residency=residency,
                exclusion=exclusion,
                employment=employment,
            )

            logger.success(f"Offender with registration number {registration_number} added to database")
            return False

        except Exception as error:
            logger.error(
                f"Error while adding offender to database: {error}"
            )

    @classmethod
    async def is_offender_exists(cls, registration_number: int) -> bool:
        try:
            if await cls.filter(registration_number=registration_number).exists():
                return True

            return False

        except:
            return False
