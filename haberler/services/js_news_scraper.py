import time
import logging
from typing import List, Dict, Optional
from django.utils.text import slugify
from django.utils import timezone
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JSNewsScrapingService:
    """
    News scraping service for JavaScript-protected websites
    Uses Selenium WebDriver to handle JavaScript rendering
    """
    
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.driver = None
        
    def _init_driver(self):
        """Initialize the Selenium WebDriver"""
        if self.driver is None:
            try:
                # Setup Chrome options
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument('--headless')  # Run in background
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                
                # Initialize the driver
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.implicitly_wait(10)
            except Exception as e:
                logger.error(f"Failed to initialize WebDriver: {e}")
                raise
    
    def _close_driver(self):
        """Close the Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
    
    def scrape_federation_news(self, federation_website):
        """
        Scrape news from a federation website that uses JavaScript rendering
        """
        try:
            logger.info(f"Scraping JavaScript-protected news from {federation_website.ad}")
            
            # Initialize the driver
            self._init_driver()
            
            # Navigate to the news page
            self.driver.get(federation_website.haberler_url)
            
            # Wait for page to load (JavaScript execution)
            time.sleep(5)  # Simple wait for JavaScript to execute
            
            # Wait for specific elements to load
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".blog-box"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for news items on {federation_website.ad}")
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find news items using the correct selector for Judo website
            news_items = soup.select(".blog-box")
            
            if not news_items:
                # Try alternative selector for the carousel items
                news_items = soup.select(".hero-single2")
                if not news_items:
                    logger.warning(f"No news items found for {federation_website.ad} using selectors: .blog-box, .hero-single2")
                    return []
            
            scraped_news = []
            
            # For automatic scraping, only get news from the last 12 hours
            time_threshold = timezone.now() - timedelta(hours=12)
            logger.info(f"Filtering news after: {time_threshold}")
            
            logger.info(f"Found {len(news_items)} news items from {federation_website.ad}")
            
            for i, item in enumerate(news_items):
                try:
                    news_data = None
                    
                    # Use specialized extraction for Judo federation
                    if 'judo.org.tr' in federation_website.haberler_url:
                        news_data = self._extract_judo_news_data(item, federation_website)
                    else:
                        # Generic extraction for other federations
                        news_data = self._extract_generic_news_data(item, federation_website)
                    
                    if news_data:
                        # For automatic scraping, only include recent news
                        if news_data.get('date'):
                            # Ensure both datetimes are timezone-aware for comparison
                            news_date = news_data['date']
                            if news_date.tzinfo is None:
                                # Make timezone-naive datetime timezone-aware
                                news_date = timezone.make_aware(news_date)
                            
                            # Compare with timezone-aware threshold
                            if news_date > time_threshold:
                                scraped_news.append(news_data)
                        else:
                            # If no date, include it (might be a new item)
                            scraped_news.append(news_data)
                            
                        logger.info(f"  {i+1}. {news_data['title']}")
                except Exception as e:
                    logger.error(f"Error extracting news item {i}: {e}")
                    continue
                    
            logger.info(f"Successfully scraped {len(scraped_news)} news items from {federation_website.ad}")
            return scraped_news
            
        except Exception as e:
            logger.error(f"Error scraping JavaScript-protected news from {federation_website.ad}: {e}")
            return []
        finally:
            # Close the driver
            self._close_driver()
    
    def _extract_generic_news_data(self, item, federation_website) -> Optional[Dict]:
        """
        Extract news data from a single news item element
        """
        try:
            # Extract title
            title_element = item.select_one(federation_website.haber_baslik_selector)
            if not title_element:
                return None
            title = title_element.get_text(strip=True)
            
            # Extract link
            link_element = item.select_one(federation_website.haber_link_selector)
            if not link_element:
                return None
                
            # Get href attribute
            href = link_element.get('href')
            if not href:
                return None
                
            # Make absolute URL
            full_url = urljoin(federation_website.ana_url, href)
            
            # Extract summary if selector is provided
            summary = ""
            if federation_website.haber_ozet_selector:
                summary_element = item.select_one(federation_website.haber_ozet_selector)
                if summary_element:
                    summary = summary_element.get_text(strip=True)
            
            # Extract date if selector is provided
            news_date = None
            if federation_website.haber_tarih_selector:
                date_element = item.select_one(federation_website.haber_tarih_selector)
                if date_element:
                    date_text = date_element.get_text(strip=True)
                    news_date = self._parse_date(date_text)
            
            return {
                'title': title[:200],  # Limit title length
                'url': full_url,
                'summary': summary[:500] if summary else title[:500],  # Use title as summary if no summary
                'date': news_date,
                'federation_website': federation_website
            }
            
        except Exception as e:
            logger.error(f"Error extracting news data: {e}")
            return None
    
    def _extract_judo_news_data(self, item, federation_website) -> Optional[Dict]:
        """
        Extract news data specifically for Judo federation website
        """
        try:
            # For Judo federation, we need to handle two different structures:
            # 1. Blog box structure (.blog-box)
            # 2. Hero carousel structure (.hero-single2)
            
            title = ""
            full_url = ""
            summary = ""
            news_date = None
            
            # Check if it's a blog box structure
            if item.select_one(".hbyuk h4"):
                # Blog box structure
                title_element = item.select_one(".hbyuk h4")
                if title_element:
                    title = title_element.get_text(strip=True)
                
                # Extract link
                link_element = item.select_one(".hbyuk a")
                if link_element and link_element.get('href'):
                    href = link_element.get('href')
                    full_url = urljoin(federation_website.ana_url, href)
                
                # Extract date
                date_element = item.select_one(".blog-meta li")
                if date_element:
                    date_text = date_element.get_text(strip=True).replace("i", "")  # Remove icon character
                    # Try to parse the date (format seems to be DD/MM/YYYY HH:MM)
                    try:
                        # Remove the icon part and extract just the date
                        date_part = date_text.split()[-2] + " " + date_text.split()[-1]  # Get date and time parts
                        news_date = datetime.strptime(date_part, "%d/%m/%Y %H:%M")
                    except:
                        pass
                        
                # Use title as summary for now
                summary = title
                
            elif item.select_one(".haberyazi"):
                # Hero carousel structure
                title_element = item.select_one(".haberyazi")
                if title_element:
                    title = title_element.get_text(strip=True)
                
                # Extract link from onclick attribute or href
                onclick_attr = item.get('onclick')
                if onclick_attr and 'window.location=' in onclick_attr:
                    # Extract URL from onclick="window.location='/haber/3301'"
                    import re
                    match = re.search(r"window\.location\s*=\s*['\"]([^'\"]+)['\"]", onclick_attr)
                    if match:
                        href = match.group(1)
                        full_url = urljoin(federation_website.ana_url, href)
                else:
                    # Try to find link in <a> tag
                    link_element = item.select_one("a")
                    if link_element and link_element.get('href'):
                        href = link_element.get('href')
                        full_url = urljoin(federation_website.ana_url, href)
                
                # Use title as summary for now
                summary = title
            else:
                # Unknown structure
                return None
            
            if not title or not full_url:
                return None
                
            return {
                'title': title[:200],  # Limit title length
                'url': full_url,
                'summary': summary[:500],  # Use title as summary
                'date': news_date,
                'federation_website': federation_website
            }
            
        except Exception as e:
            logger.error(f"Error extracting Judo news data: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse date text into datetime object
        """
        if not date_text:
            return None
            
        # Common Turkish date formats
        date_formats = [
            '%d.%m.%Y',
            '%d.%m.%Y %H:%M',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%Y.%m.%d',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
                
        # If no format matches, return None
        logger.warning(f"Could not parse date: {date_text}")
        return None
    
    def get_news_content(self, url: str) -> str:
        """
        Get full content of a news article from JavaScript-protected site
        Specifically improved for Judo federation website
        """
        try:
            # Initialize the driver
            self._init_driver()
            
            # Navigate to the news page
            self.driver.get(url)
            
            # Wait for page to load (JavaScript execution)
            time.sleep(5)
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find content with selectors specific to Judo website first
            content_selectors = [
                '.haberaciklama',      # Main content area for Judo website
                '.haber-detay',        # Alternative content area
                '.news-content',       # Generic content class
                '.post-content',       # Another common content class
                '.content',            # Generic content container
                'article',             # Semantic article tag
                '.entry-content',      # WordPress-style content
                'main'                 # Main content area
            ]
            
            content = ""
            content_element = None
            
            # Try each selector to find the main content
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Use the element with the most text content
                    best_element = max(elements, key=lambda el: len(el.get_text(strip=True)))
                    text_content = best_element.get_text(strip=True)
                    if len(text_content) > 100:  # Only use if it has substantial content
                        content_element = best_element
                        break
            
            # If we found a content element, extract its text
            if content_element:
                # Look for paragraphs first for better formatting
                paragraphs = content_element.find_all('p')
                if paragraphs:
                    # Join paragraphs with double newlines for better readability
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                else:
                    # If no paragraphs, get all text but preserve some formatting
                    content = content_element.get_text(separator='\n\n', strip=True)
            else:
                # Fallback approach: look for the element with the most text content
                body = soup.find('body')
                if body:
                    # Remove common non-content elements
                    for unwanted in body(["nav", "header", "footer", "aside", "script", "style"]):
                        unwanted.decompose()
                    
                    # Find all elements and select the one with the most text
                    candidates = body.find_all(True)
                    if candidates:
                        best_candidate = max(candidates, key=lambda el: len(el.get_text(strip=True)))
                        text_content = best_candidate.get_text(strip=True)
                        if len(text_content) > 50:  # Only use if it has reasonable content
                            content = text_content
            
            # If still no content, fallback to body text
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
            
            return content[:5000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Error getting news content from {url}: {e}")
            return ""
        finally:
            # Close the driver
            self._close_driver()
