import os

from django.db.models import Count, Sum, F
from django.http import StreamingHttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from db.learning_circle import LearningCircle, UserCircleLink
from mulearnbackend.settings import BASE_DIR
from utils.response import CustomResponse


class CommonAPI(APIView):
    def get(self, request, log_type):
        print("log type", log_type)
        log_file_path = os.path.join(BASE_DIR, 'logs', f'{log_type}.log')
        print("log file path", log_file_path)

        if os.path.exists(log_file_path):
            try:
                def file_iterator(file_path):
                    with open(file_path, 'rb') as log_file:
                        chunk_size = 8192
                        while True:
                            chunk = log_file.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk

                response = StreamingHttpResponse(file_iterator(log_file_path), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{log_type}.log"'
                return response
            except Exception as e:
                return Response({'detail': f'Error reading log file: {str(e)}'})
        else:
            return Response({'detail': f'{log_type} log file not found'})


class LcDashboardAPI(APIView):

    def get(self, request):
        date = request.GET.get('date')
        if date:
            learning_circle_count = LearningCircle.objects.filter(created_at__gt=date).count()
            total_no_enrollment = UserCircleLink.objects.filter(lead=False, accepted=True, created_at__gt=date).count()
            circle_count_by_ig = LearningCircle.objects.filter(created_at__gt=date).values('ig__name').annotate(
                total_circles=Count('id'))
        else:
            learning_circle_count = LearningCircle.objects.all().count()
            total_no_enrollment = UserCircleLink.objects.filter(lead=False, accepted=True).count()
            circle_count_by_ig = LearningCircle.objects.all().values('ig__name').annotate(
                total_circles=Count('id'))
        return CustomResponse(response={'lc_count': learning_circle_count, 'total_enrollment': total_no_enrollment,
                                        'circle_count_by_ig': circle_count_by_ig}).get_success_response()


class LcReportAPI(APIView):

    def get(self, request):
        student_info = UserCircleLink.objects.filter(lead=False, accepted=True).values(
            'user__first_name', 'user__last_name','user__mu_id',
            'circle__name', 'circle__ig__name',
            'user__user_organization_link_user__org__title',
        ).annotate(
            karma_earned=Sum(F('user__wallet_user__karma')),
        )

        return CustomResponse(response=student_info).get_success_response()
