mongoimport --host mongodb --db codeSnippets --collection course --type json --file /codeSnippets.course.json --jsonArray
mongoimport --host mongodb --db codeSnippets --collection snippets --type json --file /codeSnippets.snippets.json --jsonArray
mongoimport --host mongodb --db codeSnippets --collection comments --type json --file /codeSnippets.comments.json --jsonArray