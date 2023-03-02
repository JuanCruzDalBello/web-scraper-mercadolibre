import os
from subprocess import call
from platform import system
import tkinter as tk
import csv
import requests
from bs4 import BeautifulSoup


class MercadoLibreScraper(tk.Tk):
    def __init__(self):
        """
        Web scraper's interface.
        """
        super().__init__()

        # Set window properties
        self.title("MercadoLibre Scraper")
        self.geometry("600x300")

        # Create widgets
        self.search_label   = tk.Label(self, text="Search Term:")
        self.search_entry   = tk.Entry(self, width=40)
        self.search_button  = tk.Button(self, text="Search", command=self.search)
        self.path_label     = tk.Label(self, text="")
        self.path_entry     = tk.Entry(self, width=40, state=tk.DISABLED)
        self.data_button    = tk.Button(self, text="Copy path to clipboard", command=self.copy_path_to_clipboard)
        self.data_listbox   = tk.Listbox(self)

        # Grid layout
        self.search_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.search_entry.grid(row=0, column=1, padx=10, pady=10)
        self.search_button.grid(row=0, column=2, padx=10, pady=10)
        self.path_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.path_entry.grid(row=1, column=1, padx=10, pady=10)
        self.data_button.grid(row=1, column=2, padx=10, pady=10, columnspan=3)
        self.data_listbox.grid(row=2, column=1, padx=10, pady=10)

        self.data_listbox.bind("<Double-1>", self.open_csv)

        self._update_data_listbox()


    def _get_url(self, item):
        """
        Returns the URL of the MercadoLibre section for the given item.
        """
        return f"https://listado.mercadolibre.com.ar/{item.replace(' ', '-')}"
    

    def _get_csv_path(self, item):
        """
        Returns the path of the .csv where the data collected from the web scraping will be saved.
        """
        path = r".\busquedas"

        if not os.path.isdir(path):
            os.mkdir(path)
        
        path = rf"{path}\{item}"

        file_num = 1
        while os.path.isfile(path + str(file_num) + ".csv"):
            file_num += 1
        
        path = path + str(file_num) + ".csv"

        return path
        
    
    def _scraping(self, product):
        """
        Takes a 'bs4.element.ResultSet' object and returns a tuple with the data collected from an item.
        Output -> (product name, price, amount of reviews, URL to the product's page)
        """

        # Name
        name = product.h2.text

        print(name)

        # Amount of reviews
        try:
            amount_reviews = product.find("span", {"class": "ui-search-reviews__amount"}).text
        except AttributeError:
            amount_reviews = 0
        
        # Price
        try:
            prices = product.findAll("span", {"class": "price-tag-fraction"})

            if len(prices) > 1:
                price = prices[len(prices) - 1].text 
            else:
                price = prices[0].text

        except AttributeError:
            price = None
        
        # URL
        url = product.a["href"]

        return (name, price, amount_reviews, url)


    def _show_csv_path(self, path):
        """
        Updates the url entry widget on the interface to show where the data of the web scraping has been saved.
        Path -> ./busquedas/<archivo csv>
        """
        full_path = os.path.abspath(path)

        self.path_label.config(text="Data saved at:")
        self.path_entry.delete(0, tk.END)
        self.path_entry.config(state=tk.NORMAL)
        self.path_entry.insert(0, full_path)


    def _update_data_listbox(self):
        """
        Updates the data listbox widget of the interface to display all the files inside the 'busquedas' directory.
        """
        self.data_listbox.delete(0, tk.END)

        if not os.path.isdir(r".\busquedas"):
            return

        for file in os.listdir(r".\busquedas"):
            self.data_listbox.insert("end", file )


    def _create_blank_csv(self, path):
        """
        Creates a csv on the path given.
        The first row will display the titles of the columns:

            | Nombre | Precio | Cant. de reviews | URL |
        """
        with open(path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(("Nombre", "Precio", "Cant. de reviews", "URL"))
            pass
        


    def search(self):
        """
        Connects to the MercadoLibre website and performs the web scraping.
        """
        # List with all the products showcased con the website.
        headers  = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        item     = self.search_entry.get()
        base_url = self._get_url(item)
        response = requests.get(base_url, headers=headers)
        soup     = BeautifulSoup(response.text, features="html.parser")
        products = soup.find_all("div", {"class": "ui-search-result__wrapper"})
        
        # Create a .csv file to save all the data. 
        path = self._get_csv_path(item)
        self._create_blank_csv(path)

        # Get the data from the products on the list.
        for product in products:
            with open(path, "a", newline='') as csv_file:
                product_name, product_price, product_amount_reviews, product_url = self._scraping(product)

                writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow((product_name, " " + product_price, product_amount_reviews, product_url))

        # Show the user where the data was stored.
        self._show_csv_path(path)

        # Update the listbox widget.
        self._update_data_listbox()


    def copy_path_to_clipboard(self):
        """
        Copies the path shown on the path_entry widget to the clipboard.
        """
        self.clipboard_clear()
        self.clipboard_append(self.path_entry.get())


    def open_csv(self, _):
        """
        Opens the .csv file shown on the data_listbox widget when the user double-clicks it.
        """
        index = self.data_listbox.curselection()[0]
        file_name = self.data_listbox.get(index)
        file_path = os.path.abspath(os.path.join(r".\busquedas", file_name))
        
        if system() == "Darwin":
            call(("open", file_path))
        elif system() == "Windows":
            os.startfile(file_path)
        else:
            call(("xdg-open", file_path))


if __name__ == "__main__":
    app = MercadoLibreScraper()
    app.mainloop()
