from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(128) NOT NULL,
    `name` VARCHAR(50) NOT NULL,
    `phone` VARCHAR(20),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY `idx_users_email_133a6f` (`email`)
) CHARACTER SET utf8mb4 COMMENT='系统用户表：保存基础账号信息。';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztl21v2jAQx78KyqtO6qoQCETTNIk+TGVaYWphm1qqyMQORE2cLLHXoqrffXcmIRAIha"
    "qIVtqbNPnfXXz3OwdfH7UgpMxPjvoJi7VPlUeNk4DBzYJ+WNFIFOUqCoIMfeUowUMpZJiI"
    "mDgCRJf4CQOJssSJvUh4IUfXgWw67hCujLpwNQ1rIBtGrTmQltWAe9etkoGsu5QOpDk0QT"
    "GbLihNq66DDzUaoNTcJvqwKsTqDXhPTdcNXJ+GDiTg8dHul5Lc+yOZLcIRE2MF7uYWZI9T"
    "9sCS7DG6s12P+XSBq0fxBUq3xSRSWr/fPv2qPLGMoe2Evgx47h1NxDjkM3cpPXqEMWgbMc"
    "5iIhidw86l76ftyaRpxiCIWLJZqjQXKHOJ9LF52mdXcgd7VlEr4aX+RVtqJ65SwJ5KTshx"
    "K3hcIIvHp2lVec1K1XCpk/PW5UGt8UFVGSZiFCujIqI9qUAiyDRUcc1BsoB4/jLLkzGJV7"
    "OcBRRwQqq7AZkBehk1LSAPts/4SIzh0TDNNRh/ti4VSfBSKEP4DqdfZyc1GVMbIs0RRiRJ"
    "7sN4xY4spzgf8zogMyEnmf987AJl1bA2QAlepSiVbRGl+rsFxsz/fSI09Q0ImnopQDQVti"
    "JQ2ArgLOBFBNNvdW8AjU0AGuUAjSWATsywXJuIZYqnYBFewFaTXIws4KRp6FF280a3J9RA"
    "u9yfpL1dQ7fXvji76rUufmAlQZL88RWiVu8MLep4DyYF9aBR6MTsJZVf7d55BR8r193OWf"
    "Ecm/n1rjXMiUgR2jy8twmdOzIyNQOz0FgZ0Rc2djHyf2P32liVPE6F7t3cOIPCkDh39ySm"
    "9pIlNMIy32VTYARFhXAyUl1BtphlOtS3WOw5Y23FuJ9a1g78JPd5buIvb/MrT9BtLrYYoG"
    "FzFXd72rC9DnwjXOWjUa0361atUbfARWUyU5prdn+703tmYP4L/6dhSlscsnMh73NQ2cnY"
    "jJ/GFhBT9/cJsKpvMqmAV/mwrC/PKiEXjK84z75ddTslQ0oeUgDZ51DgDfUccVjxvUTcvk"
    "2sayhi1QtnVgbv4KL1u8j15Hv3uHgY4QuOgfFej5enf3Bv0/Y="
)
