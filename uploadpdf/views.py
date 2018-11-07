from django.shortcuts import render

# upload pdf api
from django.conf.urls import url
from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pprint import pprint
from subprocess import call, check_output, CalledProcessError, STDOUT
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource, Resource
from tastypie.utils import trailing_slash
import logging
import os.path

class uploadpdf(Resource):
    """ 
    wrapper api for checkPDFExists.py 
    usage example, call url http://asdc.immap.org/api/uploadpdf/?csv=uploadlist.csv
    """

    class Meta:
        authentication = BasicAuthentication()
        # authorization = DjangoAuthorization()
        resource_name = 'uploadpdf'
        allowed_methods = ['get', 'post']
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post']
        always_return_data = True

    def __init__(self, api_name=None):

        # init logging
        self.appfolder = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('uploadpdf')
        if not len(self.logger.handlers):
            self.logger.setLevel(logging.DEBUG)
            fh = logging.handlers.RotatingFileHandler(filename=os.path.join(self.appfolder,'uploadpdflog.txt'), mode='a', maxBytes=1024*1024, backupCount=1)
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s;%(name)s;%(funcName)s:%(lineno)d;%(levelname)s;%(message)s')
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

        super(uploadpdf, self).__init__(api_name)

    def base_urls(self):
        return [
            url(r"^%s%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('run_checkPDFExists'), name="run_checkPDFExists"),
        ]

    # @logged_in_or_basicauth()
    def run_checkPDFExists(self, request, **kwargs):

        # manual basic auth 
        auth_result = BasicAuthentication().is_authenticated(request)
        if isinstance(auth_result, bool) and (auth_result == True):
            login(request, request.user)
        else:
            return auth_result

        result = {'success': False}
        try:
            # Notes:
            # set file_out to output csv file
            # set path_upload to path of csv input
            # set file_checkPDFExists to location of checkPDFExists.py
            # make sure csv output file exist

            # path_upload = "/home/uploader/161213/"
            # path_upload = "/home/dodi/tmp/uploader/161213/"
            file_checkPDFExists = os.path.join(self.appfolder, "checkPDFExists.py")
            # filename_csv = request.GET.get('csv', '') or 'uploadlist.csv'
            # file_csv = path_upload+filename_csv
            # file_out = self.appfolder+"uploadedlist.csv"

            # print 'make sure file exist'
            # if not os.path.isfile(file_csv):
            #     raise IOError('file csv(\''+file_csv+'\') not found')
            # if not os.path.isfile(file_out):
            #     raise IOError('file output(\''+file_out+'\') not found')
            if not os.path.isfile(file_checkPDFExists):
                raise IOError('file checkPDFExists(\'%s\') not found'%(file_checkPDFExists))

            # print 'call the main script'
            # file_csv, file_out are ignored, replaced with hardcoded value
            outputtext = check_output(
                ["python", file_checkPDFExists],
                stderr=STDOUT
            )
            result['outputtext'] = outputtext

        except CalledProcessError as e:
            # print 'exception from script checkPDFExists.py'
            result['exception'] = {}
            result['exception']['name'] = 'CalledProcessError'
            if hasattr(e, 'output') and (e.output) : 
                result['exception']['output'] = e.output
                self.logger.error(result['exception']['name']+'; '+e.output)
            if hasattr(e, 'message') and (e.message) : 
                result['exception']['message'] = e.message
                self.logger.error(result['exception']['name']+'; '+e.message)
            result['exception']['returncode'] = e.returncode

        except Exception as e:
            # print 'exception not from script checkPDFExists.py'
            result['exception'] = {}
            if hasattr(e, '__name__'): 
                result['exception']['name'] = e.__name__
            result['exception']['message'] = 'exception on def run_checkPDFExists()'
            if hasattr(e, 'message'): 
                result['exception']['message'] = e.message
            self.logger.error(result['exception'].get('name', 'exception_type')+';'+e.message)

        else:
            # print 'no exception occured'
            result['success'] = True

        return self.create_response(request, result)

