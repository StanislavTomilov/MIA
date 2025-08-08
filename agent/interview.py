from transcriber.whisper import transcribe_with_faster_whisper
from prompts.templates import get_interview_prompt
from llms.llm import generate_answer

def interview_slot_pipeline(
    recorder,
    device,
    context,
    asr_model,
    llm_client
):
    recorder.start_question_recording()
    input("Нажми Enter, когда вопрос прозвучал полностью...")
    audio_path = recorder.stop_question_recording()
    question_text = transcribe_with_faster_whisper(audio_path, asr_model=asr_model)
    print(f"Вопрос: {question_text}")
    prompt = get_interview_prompt(question_text, context=context)
    answer = llm_client.generate_answer(prompt)
    print(f"\nОтвет агента: {answer}\n")
    return {"audio_path": audio_path, "question_text": question_text, "answer": answer}
