from rest_framework.response import Response
from rest_framework.views import APIView


class UsersStatusView(APIView):
    """
    users app 探活/信息接口（MVP）。
    """

    def get(self, request):
        return Response({"status": "ok", "app": "users"})

