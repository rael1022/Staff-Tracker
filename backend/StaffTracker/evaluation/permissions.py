from rest_framework import permissions

class IsAdminOrTrainer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['Admin', 'Trainer']

class IsAdminHODOrTrainer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['Admin', 'HOD', 'Trainer']

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'Admin':
            return True
        
        if request.user.role == 'Trainer' and obj.training.trainer_id == request.user.id:
            return True
        
        if request.user.role == 'HOD' and obj.user.department == request.user.department:
            return True
        
        return obj.user == request.user

class CanSubmitEvaluation(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.account_status != 'Active':
            return False
        
        return True