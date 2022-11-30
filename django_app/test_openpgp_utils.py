import unittest

import pgpy
from pgpy import errors
import openpgp_utils


class OpenPGPUtilsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_create_key(self):
        key = openpgp_utils.create_key("Test user", "test@email.com")
        self.assertEqual(type(key), pgpy.pgp.PGPKey)

    def test_protect_key_with_pass(self):
        password = "test"
        wrongpass = "wrong"
        key = openpgp_utils.create_key("Test user", "test@email.com")

        # Protect key
        openpgp_utils.lock(key, password)

        self.assertEqual(key.is_unlocked, False)

        # Try the wrong password
        with self.assertRaises(errors.PGPDecryptionError):
            with key.unlock(wrongpass) as unlocked:
                pass

        # Key should be protected now
        with key.unlock(password):
            self.assertEqual(key.is_unlocked, True)

    def test_encrypt_message(self):
        key = openpgp_utils.create_key("Test user", "test@email.com")

        # Create message and encrypt
        message = pgpy.PGPMessage.new("test")
        encrypted_message = key.pubkey.encrypt(message)

        # Check if encrypted
        self.assertEqual(encrypted_message.is_encrypted, True)

    def test_decrypt_message(self):
        key = openpgp_utils.create_key("Test user", "test@email.com")

        # Create encrypted message
        message = pgpy.PGPMessage.new("test")
        encrypted_message = key.pubkey.encrypt(message)

        # Check if encrypted
        self.assertEqual(encrypted_message.is_encrypted, True)

        # Load key from string
        priv_key = pgpy.PGPKey()
        priv_key.parse(str(key))

        decrypted_message = priv_key.decrypt(encrypted_message)

        # Decrypted message should equal original message
        self.assertEqual(decrypted_message.message, message.message)

        # Check if encrypted
        self.assertEqual(decrypted_message.is_encrypted, False)

    def test_ensure_key_not_yet_unlocked_cant_decrypt_message(self):
        key = openpgp_utils.create_key("Test user", "test@email.com")

        # Protect key
        openpgp_utils.lock(key, "test")

        # Check if locked
        self.assertEqual(key.is_unlocked, False)

        # Create and encrypt message
        message = pgpy.PGPMessage.new("test")
        encrypted_message = key.pubkey.encrypt(message)

        # Check if encrypted
        self.assertEqual(encrypted_message.is_encrypted, True)

        # Decrypt message but without unlocking key
        # Load key from string
        priv_key = pgpy.PGPKey()
        priv_key.parse(str(key))

        with self.assertRaises(errors.PGPError):
            decrypted_message = priv_key.decrypt(encrypted_message)

    def test_protect_key_with_multi_pass(self):
        password = "test"

        # With the first user we encrypt the message once
        key = openpgp_utils.create_key("Test user", "test@email.com")
        openpgp_utils.lock(key, password)
        key_2 = openpgp_utils.create_key("Test user 2", "test2@email.com")
        openpgp_utils.lock(key_2, password)

        priv_key = pgpy.PGPKey()
        priv_key.parse(str(key))
        priv_key_2 = pgpy.PGPKey()
        priv_key_2.parse(str(key_2))

        # Create and encrypt message
        message = pgpy.PGPMessage.new("test")
        encrypted_message = key.pubkey.encrypt(message)

        # Create and encrypt second message
        message_2 = pgpy.PGPMessage.new(bytes(encrypted_message))
        encrypted_message_2 = key_2.pubkey.encrypt(message_2)

        # Ensure we can decrypt
        with priv_key_2.unlock(password) as unlocked_key:
            decrypted_message_2 = unlocked_key.decrypt(encrypted_message_2)

        message_for_decryption_3 = pgpy.PGPMessage.from_blob(
            decrypted_message_2.message
        )

        with priv_key.unlock(password) as unlocked_key:
            decrypted_message_3 = unlocked_key.decrypt(message_for_decryption_3)

        self.assertEqual(message.message, decrypted_message_3.message)
