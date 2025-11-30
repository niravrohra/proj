import pandas as pd
import sys
import re
import numpy as np

def normalize_author_names(name):
    if not isinstance(name, str):
        return ''
    return re.sub(r'\s+', ' ', name.strip().lower())

def find_col_indx(header_list, possible_names):
    header_lower = [h.lower() for h in header_list]
    for name in possible_names:
        if name.lower() in header_lower:
            return header_list[header_lower.index(name.lower())]
    return None

def normalize_Borrowers(inputFile="borrowers.csv", outputFile="normalized_borrowers.csv"):
    try:
        df = pd.read_csv(inputFile, dtype=str)

        cols = list(df.columns)
        card_col = find_col_indx(cols, ['id', 'card_id', 'cardid', 'id0000id'])
        ssn_col = find_col_indx(cols, ['ssn', 'social_security_number', 'social_security'])
        first_name_col = find_col_indx(cols, ['first_name', 'firstname', 'first'])
        last_name_col = find_col_indx(cols, ['last_name', 'lastname', 'last'])
        address_col = find_col_indx(cols, ['address', 'addr', 'street'])
        city_col = find_col_indx(cols, ['city', 'town'])
        state_col = find_col_indx(cols, ['state', 'province'])
        phone_col = find_col_indx(cols, ['phone', 'phone_number', 'telephone'])

        rename_map = {
            card_col: 'Card_id',
            ssn_col: 'Ssn',
            first_name_col: 'first_name',
            last_name_col: 'last_name',
            address_col: 'Address_street',
            city_col: 'City',
            state_col: 'State',
            phone_col: 'Phone',
        }

        rename_map = {k: v for k, v in rename_map.items() if k is not None}

        if 'Card_id' not in rename_map.values() or 'Ssn' not in rename_map.values():
            raise ValueError("Essential columns missing in input file.")
    
        df = df.rename(columns=rename_map)

        first = df['first_name'].str.title().fillna('') if 'first_name' in df else ''
        last = df['last_name'].str.title().fillna('') if 'last_name' in df else ''
        df['Bname'] = (first + ' ' + last).str.strip()

        addr_part = [
            df['Address_street'].fillna('') if 'Address_street' in df else '',
            df['City'].fillna('') if 'City' in df else '',
            df['State'].fillna('') if 'State' in df else ''
        ]

        df['Address'] = pd.DataFrame(addr_part).T.apply(lambda x: ', '.join(filter(None, x)), axis=1)

        final_cols = ['Card_id']
        if 'Ssn' in df:
            final_cols.append('Ssn')
        final_cols.extend(['Bname', 'Address'])
        if 'Phone' in df:
            final_cols.append('Phone')
        
        df = df[final_cols]
        df.to_csv(outputFile, index=False)
        print(f"Normalized borrowers data written to {outputFile}")

    except FileNotFoundError:
        print(f"Input file {inputFile} not found.", file=sys.stderr)
        return
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        return
    

def normalize_Books(inputFile="books.csv", outputFile="normalized_books.csv"):

    try:
        df = pd.read_csv(inputFile, dtype= str, sep='\t')

        isbn_col = 'ISBN10'

        if isbn_col not in df.columns:
            if 'isbn13' in df.columns:
                df['ISBN10'] = df['isbn13']
            else:
                raise ValueError("No ISBN column found in input file.")
                return

        df = df.rename(columns={isbn_col: 'Isbn', 'title': 'Title', 'author': 'Author'})

        df['Title'] = df['Title'].str.title()
        df_book = df[['Isbn', 'Title']].drop_duplicates(subset=['Isbn'])
        df_book.to_csv(outputFile, index=False)
        print(f"Normalized books data written to {outputFile}")

        df_junction = df[['Isbn', 'Author']].copy()
        df_junction['Author'] = df_junction['Author'].str.split(',')
        df_junction = df_junction.explode('Author').fillna('')

        df_junction['Normalized_Name'] = df_junction['Author'].apply(normalize_author_names)
        df_junction['Original_Name'] = df_junction['Author'].str.strip()

        unique_authors_df = df_junction[df_junction['Normalized_Name'] != '']
        unique_authors_df = unique_authors_df.drop_duplicates(subset=['Normalized_Name'])

        df_authors_final = unique_authors_df[['Original_Name']].copy()
        df_authors_final = df_authors_final.rename(columns={'Original_Name': 'Name'})
        df_authors_final = df_authors_final.reset_index(drop=True)
        df_authors_final['Name'] = df_authors_final['Name'].str.title()
        df_authors_final.insert(0, 'Author_id', range(1, len(df_authors_final) + 1))

        df_authors_final.to_csv("authors.csv", index=False)
        print(f"Normalized authors data written to authors.csv")

        author_name_to_id = df_authors_final.set_index(df_authors_final['Name'].apply(normalize_author_names))['Author_id']
        df_junction['Author_id'] = df_junction['Normalized_Name'].map(author_name_to_id)
        df_final_junction = df_junction.dropna(subset=['Author_id']).copy()
        df_final_junction['Author_id'] = df_final_junction['Author_id'].astype(int)
        df_final_junction = df_final_junction[['Isbn', 'Author_id']].drop_duplicates()
        df_final_junction.to_csv("book_authors.csv", index=False)
        print(f"Normalized book-author mapping data written to book_authors.csv")

    except FileNotFoundError:
        print(f"Input file {inputFile} not found.", file=sys.stderr)
        return
    except KeyError as e:
        print(f"Missing expected column in input file: {e}", file=sys.stderr)
        return
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        return

if __name__ == "__main__":
    print("normalizing borrowers...")
    normalize_Borrowers(inputFile="borrowers.csv", outputFile="borrower.csv")
    print("normalizing books...")
    normalize_Books(inputFile="books.csv", outputFile="book.csv")
    print("Normalization complete.")
