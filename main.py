import customtkinter as ctk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from textblob import TextBlob
import speech_recognition as sr
import pyttsx3

import gui_app

def get_title(soup):
    try:
        title = soup.find("span", attrs={"id":'productTitle'}).text.strip()
    except AttributeError:
        title = ""
    return title

def get_price(soup):
    try:
        price = soup.find("span", attrs={'id':'priceblock_ourprice'}).string.strip()
    except AttributeError:
        try:
            price = soup.find("span", attrs={'id':'priceblock_dealprice'}).string.strip()
        except:
            price = ""
    return price

def get_rating(soup):
    try:
        rating = soup.find("span", attrs={'class':'a-icon-alt'}).string.strip()
    except:
        rating = ""
    return rating

def get_review_count(soup):
    try:
        review_count = soup.find("span", attrs={'id':'acrCustomerReviewText'}).string.strip()
    except:
        review_count = ""
    return review_count

def get_availability(soup):
    try:
        availability = soup.find("div", attrs={'id':'availability'}).find("span").string.strip()
    except:
        availability = "Not Available"
    return availability

def get_reviews(soup):
    reviews = soup.find_all("span", {"data-hook": "review-body"})
    review_texts = [review.get_text(strip=True) for review in reviews]
    return review_texts

def analyze_sentiment(review):
    blob = TextBlob(review)
    sentiment_score = blob.sentiment.polarity
    if sentiment_score > 0.2:
        return 'positive'
    elif sentiment_score < -0.2:
        return 'negative'
    else:
        return 'neutral'

def search_amazon_for_product(product_name):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    
    search_url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
    driver.get(search_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_link = soup.find("a", {"class": "a-link-normal s-no-outline"})
    
    if product_link:
        product_url = "https://www.amazon.in" + product_link.get("href")
    else:
        product_url = None
    
    driver.quit()
    return product_url

def perform_sentiment_analysis(product_name):
    product_url = search_amazon_for_product(product_name)
    
    if not product_url:
        return None, None, None, None, None, "Product not found.", None

    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(product_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    title = get_title(soup)
    price = get_price(soup)
    rating = get_rating(soup)
    review_count = get_review_count(soup)
    availability = get_availability(soup)
    reviews = get_reviews(soup)
    
    sentiments = [analyze_sentiment(review) for review in reviews]
    sentiment_counts = {
        'positive': sentiments.count('positive'),
        'negative': sentiments.count('negative'),
        'neutral': sentiments.count('neutral')
    }
    
    suggestion = "Suggested to buy." if sentiment_counts['positive'] > sentiment_counts['negative'] else "Consider other options."
    
    driver.quit()
    return title, price, rating, review_count, availability, suggestion, sentiment_counts

if __name__ == "__main__":
    gui_app.main()
