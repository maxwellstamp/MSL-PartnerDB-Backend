# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from google import genai
from google.genai import types
from decouple import config

# Initialize client (ideally put API key in settings.py/env variables)
client = genai.Client(api_key=config('GEMINI_API_KEY'))

@csrf_exempt
def recommend_partners(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_query = data.get('query', '')

        # prompt engineering: Instruction to return JSON only
        sys_instruction = """
        You are a business researcher. Search for firms matching the user's description.
        Return a list of at least 10 real companies with their Firm Name, Focus Area and HQ location.
        Output strictly valid JSON in this format:
        [{ 'firm name': 'firm_name',
            'headquarters': 'hq',
            'origin': 'hq',
            'focus area': 'focus_area',
            'donor experience': 'donor_experience',
            'contact': 'contact',
            'sector': 'sector',
            'current partnership status': 'current_partnership_status'}]
        """

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=user_query,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())], # ENABLES LIVE SEARCH
                    response_mime_type="application/json", # Forces JSON output
                    system_instruction=sys_instruction
                )
            )
            
            # Parse the JSON text from Gemini
            recommendations = json.loads(response.text)
            
            # Optional: Check if these partners already exist in your Postgres DB
            # for partner in recommendations:
            #     partner['is_existing'] = Partner.objects.filter(name=partner['name']).exists()

            return JsonResponse({'status': 'success', 'data': recommendations})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)