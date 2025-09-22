-- Sample FAQ Data for Campus Assistant

-- Insert categories
INSERT INTO faq_categories (id, name, description) VALUES 
    (uuid_generate_v4(), 'fees', 'Fee related queries'),
    (uuid_generate_v4(), 'scholarships', 'Scholarship information'),
    (uuid_generate_v4(), 'academics', 'Academic queries'),
    (uuid_generate_v4(), 'facilities', 'Campus facilities')
ON CONFLICT DO NOTHING;

-- Insert sample FAQs
INSERT INTO faqs (category_id, question_en, question_hi, answer_en, answer_hi, keywords) VALUES 
    (
        (SELECT id FROM faq_categories WHERE name = 'fees' LIMIT 1),
        'What are the fee payment deadlines?',
        'फीस भुगतान की अंतिम तारीख क्या है?',
        'Fee payment deadlines are: Semester 1 - July 31st, Semester 2 - December 31st. Late fees apply after these dates.',
        'फीस भुगतान की अंतिम तारीख: सेमेस्टर 1 - 31 जुलाई, सेमेस्टर 2 - 31 दिसंबर। इन तारीखों के बाद विलंब शुल्क लागू होता है।',
        ARRAY['fees', 'payment', 'deadline', 'semester']
    ),
    (
        (SELECT id FROM faq_categories WHERE name = 'scholarships' LIMIT 1),
        'What scholarships are available?',
        'कौन सी छात्रवृत्ति उपलब्ध है?',
        'Available scholarships: Merit-based (80%+ marks), Need-based (family income <2L), Sports excellence, and Minority scholarships.',
        'उपलब्ध छात्रवृत्ति: मेधा आधारित (80%+ अंक), आवश्यकता आधारित (पारिवारिक आय <2L), खेल उत्कृष्टता, और अल्पसंख्यक छात्रवृत्ति।',
        ARRAY['scholarship', 'financial aid', 'merit', 'need-based']
    )
ON CONFLICT DO NOTHING;
