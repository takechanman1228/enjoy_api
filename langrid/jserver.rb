require 'savon'
require 'wikipedia'

source_lang = "en"
target_lang = "ja"

page = Wikipedia.find('SOAP')

source = page.text
File.write('input.txt', source)

auth = %w(**** ****)

client = Savon.client(wsdl: 'http://langrid.org/service_manager/wsdl/KyotoUJServer', basic_auth: auth)

puts client.operations #=>translate
response =  client.call(:translate, message: { 'sourceLang' => source_lang, 'targetLang' => target_lang, 'source' => source})

output = response.body[:translate_response][:translate_return]
File.write('output.txt', output)
