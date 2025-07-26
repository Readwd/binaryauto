import os
import time
import asyncio
from getpass import getpass
from telegram.ext import Application, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables
driver = None
wait = None
username = None
password = None
trade_amount = None

def setup_credentials():
    """Setup credentials and trade amount"""
    global username, password, trade_amount
    
    username = os.getenv('QX_USERNAME') or input('Enter your qxbroker.com username: ')
    password = os.getenv('QX_PASSWORD') or input('Enter your qxbroker.com password: ')
    trade_amount = input('Enter trade amount: ')
    
    print(f"Username: {username}")
    print(f"Trade amount: {trade_amount}")
    print("Password: [hidden]")

def setup_browser():
    """Setup Selenium browser"""
    global driver, wait
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

def login_to_qxbroker():
    """Login to qxbroker.com"""
    try:
        print("Logging in to qxbroker.com...")
        driver.get("https://qxbroker.com")
        
        # Wait for login form and enter credentials
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = driver.find_element(By.NAME, "password")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for successful login
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard")))
        print("Successfully logged in!")
        return True
        
    except TimeoutException:
        print("Login failed - timeout")
        return False
    except Exception as e:
        print(f"Login error: {e}")
        return False

def parse_signal(message_text):
    """Extracts trading signal details from the Telegram message"""
    lines = message_text.splitlines()
    signal = {}
    for line in lines:
        if 'Active Pair' in line:
            signal['pair'] = line.split('»')[-1].strip()
        elif 'Timetable' in line:
            signal['time'] = line.split('»')[-1].strip()
        elif 'Expiration' in line:
            signal['expiration'] = line.split('»')[-1].strip()
        elif 'Direction' in line:
            signal['direction'] = line.split('»')[-1].strip()
    return signal

def select_trading_pair(pair):
    """Select the trading pair"""
    try:
        # Look for pair selector (common selectors)
        pair_selectors = [
            f"//div[contains(text(), '{pair}')]",
            f"//span[contains(text(), '{pair}')]",
            f"//option[contains(text(), '{pair}')]"
        ]
        
        for selector in pair_selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                element.click()
                print(f"Selected pair: {pair}")
                return True
            except:
                continue
                
        print(f"Could not find pair: {pair}")
        return False
        
    except Exception as e:
        print(f"Error selecting pair: {e}")
        return False

def set_expiration(expiration):
    """Set the expiration time"""
    try:
        # Convert M1, M5, etc. to minutes
        if expiration.startswith('M'):
            minutes = expiration[1:]
        else:
            minutes = expiration
            
        # Look for expiration selector
        expiration_selectors = [
            f"//div[contains(text(), '{minutes} min')]",
            f"//option[contains(text(), '{minutes}')]",
            f"//span[contains(text(), '{minutes}')]"
        ]
        
        for selector in expiration_selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                element.click()
                print(f"Set expiration: {expiration}")
                return True
            except:
                continue
                
        print(f"Could not set expiration: {expiration}")
        return False
        
    except Exception as e:
        print(f"Error setting expiration: {e}")
        return False

def set_trade_amount(amount):
    """Set the trade amount"""
    try:
        # Look for amount input field
        amount_selectors = [
            "//input[@placeholder='Amount']",
            "//input[@name='amount']",
            "//input[contains(@class, 'amount')]"
        ]
        
        for selector in amount_selectors:
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                element.clear()
                element.send_keys(amount)
                print(f"Set amount: {amount}")
                return True
            except:
                continue
                
        print(f"Could not set amount: {amount}")
        return False
        
    except Exception as e:
        print(f"Error setting amount: {e}")
        return False

def place_trade_direction(direction):
    """Place the trade in the specified direction (CALL/PUT)"""
    try:
        if direction.upper() == "CALL":
            # Look for CALL button
            call_selectors = [
                "//button[contains(text(), 'CALL')]",
                "//div[contains(text(), 'CALL')]",
                "//button[contains(@class, 'call')]"
            ]
            
            for selector in call_selectors:
                try:
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    element.click()
                    print("Placed CALL trade")
                    return True
                except:
                    continue
                    
        elif direction.upper() == "PUT":
            # Look for PUT button
            put_selectors = [
                "//button[contains(text(), 'PUT')]",
                "//div[contains(text(), 'PUT')]",
                "//button[contains(@class, 'put')]"
            ]
            
            for selector in put_selectors:
                try:
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    element.click()
                    print("Placed PUT trade")
                    return True
                except:
                    continue
        
        print(f"Could not place {direction} trade")
        return False
        
    except Exception as e:
        print(f"Error placing trade: {e}")
        return False

def place_trade(signal):
    """Main function to place trade based on signal"""
    try:
        print(f"Processing signal: {signal}")
        
        # Login if not already logged in
        if "dashboard" not in driver.current_url:
            if not login_to_qxbroker():
                return False
        
        # Navigate to trading page if needed
        if "trading" not in driver.current_url:
            driver.get("https://qxbroker.com/trading")
            time.sleep(2)
        
        # Execute trading steps
        if not select_trading_pair(signal['pair']):
            return False
            
        if not set_expiration(signal['expiration']):
            return False
            
        if not set_trade_amount(trade_amount):
            return False
            
        if not place_trade_direction(signal['direction']):
            return False
        
        print(f"✅ Trade placed successfully!")
        print(f"   Pair: {signal['pair']}")
        print(f"   Direction: {signal['direction']}")
        print(f"   Expiration: {signal['expiration']}")
        print(f"   Amount: {trade_amount}")
        print(f"   Time: {signal['time']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error placing trade: {e}")
        return False

async def handle_message(update, context):
    """Telegram message handler"""
    text = update.message.text
    if 'Active Pair' in text and 'Direction' in text:
        signal = parse_signal(text)
        # Run the trading function in a separate thread to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, place_trade, signal)

async def main():
    """Main function"""
    # Setup credentials and browser
    setup_credentials()
    setup_browser()
    
    # Get Telegram token
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or input('Enter your Telegram bot token: ')
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print('Bot is running. Waiting for signals...')
    
    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())