# Asyncwiki

--------------------

## About
### The library for async work with Wikipedia

Some words about library

- Asynchronous
- Fast (probably)
- Parse Wikipedia
- Can work with databases
- And it`s all

## Installation

You can install <code>asyncwiki</code> from PyPI:

    pip install asyncwiki

## Quick start

A little example of library work:

    import asyncio
    from asyncwiki import WikiSearcher

    
    wiki_searcher = WikiSearcher()
    

    async def main():
        
        query = "Apple"
        lang = "en"

        result = await wiki_searcher.search(query, lang)
        print(result)

    
    if __name__ == "__main__":
        asyncio.run(main())

## License
<code>Asyncwiki</code> is offered under the MIT license.
