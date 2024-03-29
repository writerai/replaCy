from typing import List

from replacy import ESpan


def filter_0distance(spans: List[ESpan]) -> List[ESpan]:
    filtered_spans = []
    for span in spans:
        if len(span.suggestions):
            suggestions = []
            for suggestion in span.suggestions:
                if (span.doc[span.start:span.end].text) == suggestion:
                    continue
                suggestions.append(suggestion)

            if len(suggestions):
                span.suggestions = suggestions
                filtered_spans.append(span)
        else:
            filtered_spans.append(span)
    return filtered_spans


def filter_0distance_with_line_break(spans: List[ESpan]) -> List[ESpan]:
    filtered_spans = []
    for span in spans:
        if len(span.suggestions):
            span_text = span.doc[span.start:span.end].text.rstrip(" \r\n")
            suggestions = []
            for suggestion in span.suggestions:
                if span_text == suggestion:
                    continue
                suggestions.append(suggestion)

            if len(suggestions):
                span.suggestions = suggestions
                filtered_spans.append(span)
        else:
            filtered_spans.append(span)
    return filtered_spans