import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import speech_recognition as sr
import pyttsx3
from main import perform_sentiment_analysis, search_amazon_for_product
import customtkinter as ctk

class SentimentAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Amazon Product Sentiment Analysis")
        self.root.geometry("1400x900")
        
        # Set theme and colors
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=('Helvetica', 24, 'bold'), padding=20)
        self.style.configure("Subtitle.TLabel", font=('Helvetica', 12), padding=10)
        self.style.configure("Result.TLabel", font=('Helvetica', 11))
        self.style.configure("Custom.TButton", font=('Helvetica', 11, 'bold'))
        
        # Setup scrollable canvas
        self.setup_scrollable_canvas()
        self.setup_gui_elements()
        self.setup_voice_assistant()
        
    def setup_scrollable_canvas(self):
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollbar_y = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollbar_y.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)
        
        self.scrollbar_x = ttk.Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.scrollbar_x.pack(side="bottom", fill="x")
        self.canvas.configure(xscrollcommand=self.scrollbar_x.set)
        
        self.canvas_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")
        
        self.canvas_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def setup_gui_elements(self):
        main_container = ttk.Frame(self.canvas_frame, padding="20")
        main_container.grid(row=0, column=0, sticky="nsew")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame,
            text="Amazon Product Sentiment Analysis",
            style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2)
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Analyze product sentiments using voice or text search",
            style="Subtitle.TLabel"
        )
        subtitle_label.grid(row=1, column=0, columnspan=2)
        
        search_frame = ttk.LabelFrame(main_container, text="Search Product", padding="15")
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.voice_status = ttk.Label(
            search_frame,
            text="🎤 Ready",
            font=('Helvetica', 10)
        )
        self.voice_status.grid(row=0, column=0, padx=5)
        
        self.product_entry = ttk.Entry(
            search_frame,
            width=60,
            font=('Helvetica', 12)
        )
        self.product_entry.grid(row=0, column=1, padx=10)
        
        buttons_frame = ttk.Frame(search_frame)
        buttons_frame.grid(row=0, column=2)
        
        self.voice_button = ttk.Button(
            buttons_frame,
            text="Voice Search",
            command=self.start_voice_search,
            style="Custom.TButton"
        )
        self.voice_button.grid(row=0, column=0, padx=5)
        
        analyze_button = ttk.Button(
            buttons_frame,
            text="Analyze",
            command=self.start_analysis,
            style="Custom.TButton"
        )
        analyze_button.grid(row=0, column=1, padx=5)
        
        results_frame = ttk.LabelFrame(main_container, text="Analysis Results", padding="15")
        results_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        self.setup_product_details(results_frame)
        
        charts_frame = ttk.LabelFrame(main_container, text="Sentiment Visualization", padding="15")
        charts_frame.grid(row=2, column=1, sticky="nsew")
        self.setup_charts(charts_frame)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            main_container,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=200
        )
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", pady=20)
        
        self.status_label = ttk.Label(
            main_container,
            text="Ready to analyze",
            font=('Helvetica', 10),
            foreground='gray'
        )
        self.status_label.grid(row=4, column=0, columnspan=2)

    def setup_product_details(self, parent):
        details_frame = ttk.Frame(parent)
        details_frame.pack(fill="both", expand=True)
        
        self.details_vars = {
            'Title': tk.StringVar(),
            'Price': tk.StringVar(),
            'Rating': tk.StringVar(),
            'Review Count': tk.StringVar(),
            'Availability': tk.StringVar(),
            'Sentiment': tk.StringVar()
        }
        
        for idx, (label, var) in enumerate(self.details_vars.items()):
            detail_frame = ttk.Frame(details_frame)
            detail_frame.pack(fill="x", pady=5)
            
            ttk.Label(
                detail_frame,
                text=f"{label}:",
                style="Result.TLabel",
                width=15
            ).pack(side="left")
            
            ttk.Label(
                detail_frame,
                textvariable=var,
                style="Result.TLabel"
            ).pack(side="left", fill="x", expand=True)

    def setup_charts(self, parent):
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def setup_voice_assistant(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        
    def start_voice_search(self):
        def voice_input():
            try:
                self.voice_status.config(text="🎤 Listening...", foreground="blue")
                self.voice_button.config(state="disabled")
                self.progress_var.set(20)
                
                with sr.Microphone() as source:
                    self.status_label.config(text="Adjusting for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
                    self.status_label.config(text="Listening... Speak now!")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                self.progress_var.set(50)
                self.status_label.config(text="Processing speech...")
                
                product_name = self.recognizer.recognize_google(audio)
                self.progress_var.set(80)
                
                self.product_entry.delete(0, tk.END)
                self.product_entry.insert(0, product_name)
                self.progress_var.set(100)
                
                self.voice_status.config(text="🎤 Voice input received", foreground="green")
                self.status_label.config(text=f"Recognized: {product_name}")
                
                self.start_analysis()
                
            except sr.WaitTimeoutError:
                self.status_label.config(text="No speech detected. Please try again.")
            except sr.UnknownValueError:
                self.status_label.config(text="Could not understand audio. Please try again.")
            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)}")
            finally:
                self.voice_button.config(state="normal")
                self.voice_status.config(text="🎤 Ready")
                self.progress_var.set(0)
        
        threading.Thread(target=voice_input, daemon=True).start()
        
    def start_analysis(self):
        def analyze():
            try:
                self.progress_var.set(20)
                product_name = self.product_entry.get()
                
                if not product_name:
                    messagebox.showerror("Error", "Please enter a product name")
                    return
                
                self.status_label.config(text="Analyzing product...")
                title, price, rating, review_count, availability, suggestion, sentiment_counts = perform_sentiment_analysis(product_name)
                self.progress_var.set(60)
                
                if title:
                    # Update product details
                    self.details_vars['Title'].set(title)
                    self.details_vars['Price'].set(price if price else "Price not available")
                    self.details_vars['Rating'].set(rating if rating else "No rating")
                    self.details_vars['Review Count'].set(review_count if review_count else "No reviews")
                    self.details_vars['Availability'].set(availability)
                    self.details_vars['Sentiment'].set(suggestion)
                    
                    # Update charts with sentiment counts
                    self.update_charts(sentiment_counts)
                    self.progress_var.set(100)
                    self.status_label.config(text="Analysis completed successfully!")
                    
                    # Voice feedback
                    self.engine.say(f"Analysis complete. {suggestion}")
                    self.engine.runAndWait()
                else:
                    self.status_label.config(text="Product not found. Please try another search.")
                    self.progress_var.set(0)
                
            except Exception as e:
                self.status_label.config(text=f"Analysis failed: {str(e)}")
                self.progress_var.set(0)
        
        threading.Thread(target=analyze, daemon=True).start()

        
    def update_charts(self, sentiment_counts):
    # Clear previous charts
        self.ax1.clear()
        self.ax2.clear()

        sentiments = list(sentiment_counts.keys())
        counts = list(sentiment_counts.values())
        colors = ['#4CAF50', '#F44336', '#2196F3']  # Green, Red, Blue

        # Bar chart
        bars = self.ax1.bar(sentiments, counts, color=colors)
        self.ax1.set_title('Sentiment Distribution', pad=15)
        self.ax1.set_ylabel('Number of Reviews')
        self.ax1.tick_params(axis='x', rotation=0)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            self.ax1.text(bar.get_x() + bar.get_width() / 2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')

        # Pie chart
        patches, texts, autotexts = self.ax2.pie(
            counts, labels=sentiments, colors=colors,
            autopct='%1.1f%%', startangle=90
        )
        self.ax2.set_title('Sentiment Ratio', pad=15)

        # Equal aspect ratio ensures that pie is drawn as a circle
        self.ax2.axis('equal')

        # Refresh canvas
        self.figure.tight_layout()
        self.canvas.draw()


def main():
    root = tk.Tk()
    app = SentimentAnalysisGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()