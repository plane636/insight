
#-*- coding:utf-8 -*-

from flask import render_template, flash, url_for, redirect, request, current_app, session, jsonify, abort
from .forms import VulReportForm, VulReportReviewForm, VulReportAdminForm
from .forms import VulReportDevFinishForm, VulReportRetestResultForm, VulReportSendEmailForm
from .forms import VulReportAttackForm, VulReportVulCataForm
from .models import VulReport, VulLog
from ..admin.models import Asset, User, Depart
from ..admin.forms import AssetForm
from .. import db
import datetime
import json
from flask_login import current_user, login_required
from werkzeug import secure_filename
from ..email import send_email
from ..decorators import permission_required
from sqlalchemy import or_
from ..auth.models import LoginUser
from . import src




#-------------漏洞报告模块------------------------------------------------------------------------------

''' 漏洞报告管理编辑页面 '''
@src.route('/vul_report_admin_edit/<id>', methods=['GET', 'POST'])
@permission_required('src.vul_report_admin_edit')
def vul_report_admin_edit(id):
	form = VulReportAdminForm()
	vul_report = VulReport.query.get_or_404(id)
	if form.validate_on_submit():
		vul_report.title = form.title.data
		vul_report.related_asset = form.related_asset.data
		vul_report.related_asset_inout = form.related_asset_inout.data
		vul_report.related_asset_status = form.related_asset_status.data
		vul_report.related_vul_cata = form.related_vul_cata.data
		vul_report.related_vul_type = form.related_vul_type.data
		vul_report.vul_self_rank = int(form.vul_self_rank.data)
		vul_report.vul_source = form.vul_source.data
		vul_report.vul_poc = form.vul_poc.data
		#vul_report.vul_poc_html = form.vul_poc_html.data 
		vul_report.vul_solution = form.vul_solution.data
		#vul_report.vul_solution_html = form.vul_solution_html.data
		if form.grant_rank.data != '':
			vul_report.grant_rank = int(form.grant_rank.data)
		vul_report.vul_type_level = form.vul_type_level.data
		if form.risk_score.data != '': 
			vul_report.risk_score = float(form.risk_score.data)
		#vul_report.person_score = form.person_score.data
		vul_report.done_solution = form.done_solution.data
		if form.done_rank.data != '':
			vul_report.done_rank = int(form.done_rank.data)
		if form.residual_risk_score.data != '':
			vul_report.residual_risk_score = float(form.residual_risk_score.data)
		vul_report.vul_status = form.vul_status.data
		if form.start_date.data !='':
			vul_report.start_date = form.start_date.data
		if form.end_date.data != '':
			vul_report.end_date = form.end_date.data
		if form.fix_date.data != '':
			vul_report.fix_date = form.fix_date.data
		vul_report.attack_check = form.attack_check.data
		flash(u'更新漏洞 %s 报告成功!' %vul_report.title)
		redirect(url_for('src.vul_report_admin_edit', id=vul_report.id))

	form.title.data = vul_report.title
	form.related_asset.data = vul_report.related_asset
	form.related_asset_inout.data = vul_report.related_asset_inout
	form.related_asset_status.data = vul_report.related_asset_status
	form.related_vul_cata.data = vul_report.related_vul_cata
	form.related_vul_type.data = vul_report.related_vul_type
	form.vul_self_rank.data = vul_report.vul_self_rank
	form.vul_source.data = vul_report.vul_source
	form.vul_poc.data = vul_report.vul_poc
	#form.vul_poc_html.data = vul_report.vul_poc_html
	form.vul_solution.data = vul_report.vul_solution
	#form.vul_solution_html.data = vul_report.vul_solution_html
	form.grant_rank.data = vul_report.grant_rank
	form.vul_type_level.data = vul_report.vul_type_level
	form.risk_score.data = vul_report.risk_score
	form.person_score.data = vul_report.person_score
	form.done_solution.data = vul_report.done_solution
	form.done_rank.data = vul_report.done_rank
	form.residual_risk_score.data = vul_report.residual_risk_score
	form.vul_status.data = vul_report.vul_status
	form.start_date.data = vul_report.start_date
	form.end_date.data = vul_report.end_date
	form.fix_date.data = vul_report.fix_date
	form.attack_check.data = vul_report.attack_check
	return render_template('src/vul_report_admin_edit.html', form=form)


''' 漏洞报告提交页面 '''
@src.route('/vul_report_add', methods=['GET', 'POST'])
@login_required
@permission_required('src.vul_report_add')
def vul_report_add():
	form = VulReportForm()
	if form.validate_on_submit():
		# 漏洞报告提交时判断关联资产是否存在，若不存在则返回500
		asset_get = Asset.query.filter_by(domain=form.related_asset.data).first()
		if asset_get is None:
			return abort(500)

		vul_rpt = VulReport(author=current_user.email, 
					title = form.title.data,
					related_asset = form.related_asset.data,
					related_asset_inout = asset_get.in_or_out,
					related_asset_status = asset_get.status,
					related_vul_cata = form.related_vul_cata.data,
					related_vul_type = form.related_vul_type.data,
					vul_self_rank = form.vul_self_rank.data,
					vul_source = form.vul_source.data,
					vul_poc = form.vul_poc.data,
					vul_solution  = form.vul_solution.data,
					)
		db.session.add(vul_rpt)
		flash(u'漏洞报告 %s-%s 提交成功' %(current_user.username, form.title.data))

		#创建后的漏洞报告，获取ID
		vul_report = VulReport.query.filter_by(title=vul_rpt.title).order_by(VulReport.id.desc()).first()

		#记录漏洞日志
		vul_log = VulLog(related_vul_id = vul_report.id,
						related_user_email = current_user.email,
						action = u'提交漏洞报告',
					)
		db.session.add(vul_log)

		#发送邮件给安全管理员，和漏洞提交人员
		#安全管理员邮箱获取
		query = LoginUser.query.filter_by(role_name=u'安全管理员')
		to_email_list = []
		if query.first():
			for lg_user in query.all():
				to_email_list.append(lg_user.email)
			send_email(u'新漏洞等待审核', 'src/email/new_vul_submit', to=to_email_list, cc=current_app.config['CC_EMAIL'], vul_report=vul_report)
			flash(u'等待审核的邮件已发送给安全管理员！')
		else:
			flash(u'安全管理员未设置!')

		# 漏洞报告提交成功后跳转到漏洞报告查看页面
		return redirect(url_for('src.vul_report_list_read'))
	return render_template('src/vul_report_add.html', form=form)

#-----------------------上传图片----------------------------------------------------------

''' 上传图片后缀白名单设置 '''
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xmind'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


''' 上传图片功能请求 '''
@src.route('/upload_img', methods=['POST'])
@permission_required('src.upload_img')
def upload_img():
	up_img_file = request.files['upload']
	if up_img_file and allowed_file(up_img_file.filename):
		# 获取上传图片的后缀类型
		img_type = up_img_file.filename.rsplit('.', 1)[1]
		# 重新格式化命名图片文件名
		save_filename = datetime.datetime.now().strftime('%Y%m%d%H%M%s') + '.' + img_type
		''' 根据文件后缀类型选择存储目录 '''
		if img_type == 'xlsx':
			up_img_file.save(current_app.config['UPLOAD_EXCEL_FOLDER'] + save_filename)
			# 将文件存储后的路径和文件名保存在session中
			session['filename'] = url_for('src.static', filename='upload/excel/'+save_filename)
		elif img_type == 'xmind':
			up_img_file.save(current_app.config['UPLOAD_XMIND_FOLDER'] + save_filename)
			session['filename'] = url_for('src.static', filename='upload/xmind/'+save_filename)
		else:
			up_img_file.save(current_app.config['UPLOAD_IMG_FOLDER'] + save_filename)
			session['filename'] = url_for('src.static', filename='upload/img/'+save_filename)
		# 返回文件路径
		return jsonify(filename=session['filename'])


''' 漏洞报告查看页面 '''
''' 未登录的用户只允许查看状态为【完成】的漏洞报告列表，且不能查看输出文档 '''
''' 登录状态下，管理员和安全人员角色可以查看全部的漏洞报告列表，其它角色权限和未登录用户查看漏洞报告列表权限相同 '''
@src.route('/vul_report_list_read', methods=['GET', 'POST'])
def vul_report_list_read():
	opt = request.args.get('opt','all')

	if current_user.is_authenticated:
		if current_user.role_name==u'安全管理员' or current_user.role_name==u'超级管理员' or current_user.role_name==u'安全人员':
			#query = VulReport.query
			query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														)
		else:
			#query = VulReport.query.filter(VulReport.vul_status==u'完成', VulReport.related_vul_type!=u'输出文档')
			query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
															VulReport.vul_status==u'完成',
															VulReport.related_vul_type!=u'输出文档',
														)
	else:
		#query = VulReport.query.filter(VulReport.vul_status==u'完成', VulReport.related_vul_type!=u'输出文档')
		query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														VulReport.vul_status==u'完成',
														VulReport.related_vul_type!=u'输出文档',
														)

	''' 逾期完成、逾期未完成为精确匹配搜索，其它搜索关键字为模糊搜索 '''
	if opt=='all':
		vul_report_list_result = query.order_by(-VulReport.start_date).all()
	elif opt==u'逾期完成':
		vul_report_list_result = query.filter(VulReport.vul_status == u'完成',
											VulReport.fix_date > VulReport.end_date,
											VulReport.related_vul_type != u'输出文档',
											).order_by(-VulReport.start_date)
	elif opt==u'逾期未完成':
		vul_report_list_result = query.filter(VulReport.vul_status != u'完成',
											datetime.date.today() > VulReport.end_date,
											VulReport.related_vul_type != u'输出文档',
											).order_by(-VulReport.start_date)
	else:
		vul_report_list_result = query.filter(VulReport.author.like("%" + opt + "%")
											| VulReport.title.like("%" + opt + "%")
											| (VulReport.related_asset == opt)
											| VulReport.related_asset_inout.like("%" + opt + "%")
											| VulReport.related_asset_status.like("%" + opt + "%")
											| VulReport.related_vul_cata.like("%" + opt + "%")
											| VulReport.related_vul_type.like("%" + opt + "%")
											| VulReport.vul_source.like("%" + opt + "%")
											| VulReport.vul_status.like("%" + opt + "%")
											| Asset.department.like("%" + opt + "%")
											).order_by(-VulReport.start_date)
	return render_template('src/vul_report_list_read.html', vul_report_list_result=vul_report_list_result)


''' 所有漏洞日志查看页面 '''
@src.route('/vul_report_log_read', methods=['GET',])
@login_required
def vul_report_log_read():
	opt = request.args.get('opt','all')
	page = request.args.get('page', 1, type=int)

	''' 分页，每页显示SRCPM_PER_PAGE=10条 '''
	pagination = VulLog.query.order_by(-VulLog.time).paginate(
                        page, per_page=current_app.config['SRCPM_PER_PAGE'], error_out=False
                        )
	vul_report_log_result = pagination.items

	dict_vul_title = {}
	for vul_log in vul_report_log_result:
		vul_report_title = VulReport.query.get(vul_log.related_vul_id).title
		dict_vul_title.update({vul_log.related_vul_id : vul_report_title})

	
	return render_template('src/vul_report_log_read.html', 
							vul_report_log_result=vul_report_log_result, 
							pagination=pagination,
							opt=opt,
							dict_vul_title=dict_vul_title,
							)


#-----------------------------------分用户漏洞管理---------------------------------------

''' 未审核漏洞列表页面 '''
@src.route('/vul_review_list', methods=['GET', 'POST'])
@permission_required('src.vul_review_list')
def vul_review_list():
	query = VulReport.query.filter_by(vul_status=u'未审核').order_by(-VulReport.start_date)

	#处理post查询提交
	opt_label = [u'查询', u'请输入关键字进行查询']
	if request.method == 'POST':
		opt = request.form.get('opt','all')
		#输入send_email_password则忽略，不发送邮件提醒
		#输入不是send_email_password则进行模糊查询
		if opt != 'send_email_password':
			query = query.filter(VulReport.author.like("%" + opt + "%")
									| VulReport.title.like("%" + opt + "%")
									| VulReport.related_asset.like("%" + opt + "%")
									| VulReport.related_asset_inout.like("%" + opt + "%")
									| VulReport.related_asset_status.like("%" + opt + "%")
									| VulReport.related_vul_cata.like("%" + opt + "%")
									| VulReport.related_vul_type.like("%" + opt + "%")
									| VulReport.vul_source.like("%" + opt + "%")
									| VulReport.vul_status.like("%" + opt + "%")
								)
		elif opt=='send_email_password' and current_user.role_name==u'安全管理员':
			pass

	if current_user.role_name == u'超级管理员' or current_user.role_name == u'安全管理员':
		vul_report_list = query.all()
	elif current_user.role_name == u'安全人员':
		vul_report_list = query.filter_by(author=current_user.email).all()
	return render_template('src/vul_review_list.html', vul_report_list=vul_report_list, opt_label=opt_label)


''' 已通告漏洞列表页面 '''
@src.route('/vul_notify_list', methods=['GET', 'POST'])
@login_required
def vul_notify_list():
	query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														VulReport.vul_status==u'已通告').order_by(-VulReport.start_date)
	opt_label = [u'查询', u'请输入关键字进行查询']

	if request.method == 'POST':
		opt = request.form.get('opt','all')
		if opt != 'send_email_password':
			# 输入不是send_email_password，则进行模糊查询
			query = query.filter(VulReport.author.like("%" + opt + "%")
									| VulReport.title.like("%" + opt + "%")
									| VulReport.related_asset.like("%" + opt + "%")
									| VulReport.related_asset_inout.like("%" + opt + "%")
									| VulReport.related_asset_status.like("%" + opt + "%")
									| VulReport.related_vul_type.like("%" + opt + "%")
									| VulReport.vul_source.like("%" + opt + "%")
									| VulReport.vul_status.like("%" + opt + "%")
								)
		elif opt=='send_email_password':
			# 输入send_email_password则发送提醒邮件，只有管理员有权限发送提醒邮件
			if current_user.role_name==u'安全管理员' or current_user.role_name==u'超级管理员':
				# 设置发送邮件的列表
				list_to_send_email = []
				for vul_report in query.all():
					email_dict = get_email_dict(vul_report[0].id)
					email_list = []
					email_list = email_dict['owner']
					email_list.append(email_dict['department_manager'])
					email_list.append(email_dict['author'])
					if email_list not in list_to_send_email:
						list_to_send_email.append(email_list)

				# 遍历发送邮件列表，发送提醒邮件
				for e_l in list_to_send_email:
					send_email(u'新通告漏洞提醒',
								'src/email/vul_notify_mail_alert',
								to=e_l,
								cc=current_app.config['CC_EMAIL'],
								)
					flash(u'给 %s 的提醒邮件已发出!' %e_l[0])


	if current_user.role_name == u'超级管理员' or current_user.role_name == u'安全管理员':
		vul_report_list = query.all()
		opt_label = [u'发送邮件', u'请输入密码发送邮件']
	elif current_user.role_name == u'安全人员':
		vul_report_list = query.filter(VulReport.author==current_user.email).all()
	elif current_user.role_name == u'普通用户':
		# 判断普通用户是否为部门经理，部门经理有权限查看部门所有漏洞
		department_list = Depart.query.filter_by(email=current_user.email).all()
		if department_list:
			vul_report_list = []
			for department in department_list:
				vul_report_list += query.filter(Asset.department==department.department).all()
		else:
			vul_report_list = query.filter(Asset.owner.like("%" + current_user.email + "%")).all()
	return render_template('src/vul_notify_list.html', vul_report_list=vul_report_list, opt_label=opt_label)


''' 修复中漏洞列表页面 '''
@src.route('/vul_processing_list', methods=['GET', 'POST'])
@login_required
def vul_processing_list():
	query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														VulReport.vul_status==u'修复中').order_by(-VulReport.start_date)
	#处理post查询提交
	opt_label = [u'查询', u'请输入关键字进行查询']
	if request.method == 'POST':
		opt = request.form.get('opt','all')
		if opt != 'send_email_password':
			# 输入不是send_email_password，则进行模糊查询
			query = query.filter(VulReport.author.like("%" + opt + "%")
									| VulReport.title.like("%" + opt + "%")
									| VulReport.related_asset.like("%" + opt + "%")
									| VulReport.related_asset_inout.like("%" + opt + "%")
									| VulReport.related_asset_status.like("%" + opt + "%")
									| VulReport.related_vul_type.like("%" + opt + "%")
									| VulReport.vul_source.like("%" + opt + "%")
									| VulReport.vul_status.like("%" + opt + "%")
								)
		elif opt=='send_email_password':
			# 输入send_email_password则发送提醒邮件，只有管理员有权限发送提醒邮件
			if current_user.role_name==u'超级管理员' or current_user.role_name==u'安全管理员':
				#设置发送邮件的列表
				list_to_send_email = []
				for vul_report in query.all():
					email_dict = get_email_dict(vul_report[0].id)
					email_list = email_dict['owner']
					email_list.append(email_dict['department_manager'])
					email_list.append(email_dict['author'])
					if email_list not in list_to_send_email:
						list_to_send_email.append(email_list)

				#遍历发送邮件列表，发送提醒邮件
				for e_l in list_to_send_email:
					send_email(u'修复中漏洞提醒',
								'src/email/vul_processing_mail_alert',
								to=e_l,
								cc=current_app.config['CC_EMAIL'],
								)
					flash(u'给 %s 的提醒邮件已发出!' %e_l[0])		

	if current_user.role_name == u'超级管理员' or current_user.role_name == u'安全管理员':
		vul_report_list = query.all()
		opt_label = [u'发送邮件', u'请输入密码发送邮件']
	elif current_user.role_name == u'安全人员':
		vul_report_list = query.filter(VulReport.author==current_user.email).all()
	elif current_user.role_name == u'普通用户':
		#查询用户email是否为部门经理，可能为多个部门经理。
		department_list = Depart.query.filter_by(email=current_user.email).all()
		#如果是部门经理，则可查看部门漏洞
		if department_list:
			vul_report_list = []
			for department in department_list:
				vul_report_list += query.filter(Asset.department==department.department).all()
		else:
			query = query.filter(Asset.owner.like("%" + current_user.email + "%"))
			vul_report_list = query.all()

	return render_template('src/vul_processing_list.html', vul_report_list=vul_report_list, opt_label=opt_label)


''' 修复中暂不处理漏洞列表页面 '''
@src.route('/vul_processing_noalert_list', methods=['GET', 'POST'])
@login_required
def vul_processing_noalert_list():
	query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														VulReport.vul_status==u'暂不处理').order_by(-VulReport.start_date)
	#处理post查询提交
	opt_label = [u'查询', u'请输入关键字进行查询']
	if request.method == 'POST':
		opt = request.form.get('opt','all')
		if opt != 'send_email_password':
			query = query.filter(VulReport.author.like("%" + opt + "%")
									| VulReport.title.like("%" + opt + "%")
									| VulReport.related_asset.like("%" + opt + "%")
									| VulReport.related_asset_inout.like("%" + opt + "%")
									| VulReport.related_asset_status.like("%" + opt + "%")
									| VulReport.related_vul_type.like("%" + opt + "%")
									| VulReport.vul_source.like("%" + opt + "%")
									| VulReport.vul_status.like("%" + opt + "%")
								)
		elif opt=='send_email_password':
			# 输入send_email_password则发送提醒邮件，只有管理员有权限发送提醒邮件
			if current_user.role_name==u'超级管理员' or current_user.role_name==u'安全管理员':
				#设置发送邮件的列表
				list_to_send_email = []
				for vul_report in query.all():
					email_dict = get_email_dict(vul_report[0].id)
					email_list = email_dict['owner']
					email_list.append(email_dict['department_manager'])
					email_list.append(email_dict['author'])
					if email_list not in list_to_send_email:
						list_to_send_email.append(email_list)

				#遍历发送邮件列表，发送提醒邮件
				for e_l in list_to_send_email:
					send_email(u'暂不处理漏洞提醒',
								'src/email/vul_processing_noalert_mail_alert',
								to=e_l,
								cc=current_app.config['CC_EMAIL'],
								)
					flash(u'给 %s 的提醒邮件已发出!' %e_l[0])		

	if current_user.role_name == u'超级管理员' or current_user.role_name == u'安全管理员':
		vul_report_list = query.all()
		opt_label = [u'发送邮件', u'请输入密码发送邮件']
	elif current_user.role_name == u'安全人员':
		vul_report_list = query.filter(VulReport.author==current_user.email).all()
	elif current_user.role_name == u'普通用户':
		#查询用户email是否为部门经理，可能为多个部门经理。
		department_list = Depart.query.filter_by(email=current_user.email).all()
		#如果是部门经理，则可查看部门漏洞
		if department_list:
			vul_report_list = []
			for department in department_list:
				vul_report_list += query.filter(Asset.department==department.department).all()
		else:
			query = query.filter(Asset.owner.like("%" + current_user.email + "%"))
			vul_report_list = query.all()

	return render_template('src/vul_processing_noalert_list.html', vul_report_list=vul_report_list, opt_label=opt_label)


''' 复测中漏洞列表页面 '''
@src.route('/vul_retest_list', methods=['GET', 'POST'])
@login_required
def vul_retest_list():
	query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														VulReport.vul_status==u'复测中').order_by(-VulReport.start_date)

	#处理post提交
	opt_label = [u'查询', u'请输入关键字进行查询']
	if request.method == 'POST':
		opt = request.form.get('opt','all')
		if opt != 'send_email_password':
			query = query.filter(VulReport.author.like("%" + opt + "%")
									| VulReport.title.like("%" + opt + "%")
									| VulReport.related_asset.like("%" + opt + "%")
									| VulReport.related_asset_inout.like("%" + opt + "%")
									| VulReport.related_asset_status.like("%" + opt + "%")
									| VulReport.related_vul_type.like("%" + opt + "%")
									| VulReport.vul_source.like("%" + opt + "%")
									| VulReport.vul_status.like("%" + opt + "%")
								)
		elif opt=='send_email_password':
			if current_user.role_name==u'超级管理员' or current_user.role_name==u'安全管理员':
				pass

	if current_user.role_name == u'超级管理员' or current_user.role_name == u'安全管理员':
		vul_report_list = query.all()
	elif current_user.role_name == u'安全人员':
		vul_report_list = query.filter(VulReport.author==current_user.email).all()
	elif current_user.role_name == u'普通用户':
		department_list = Depart.query.filter_by(email=current_user.email).all()
		if department_list:
			vul_report_list = []
			for department in department_list:
				vul_report_list += query.filter(Asset.department==department.department).all()
		else:
			vul_report_list = query.filter(Asset.owner.like("%" + current_user.email + "%")).all()

	return render_template('src/vul_retest_list.html', vul_report_list=vul_report_list, opt_label=opt_label)


''' 已完成漏洞列表页面 '''
@src.route('/vul_finished_list', methods=['GET', 'POST'])
@login_required
def vul_finished_list():
	query = db.session.query(VulReport, Asset).filter(VulReport.related_asset==Asset.domain,
														VulReport.vul_status==u'完成').order_by(-VulReport.start_date)

	#处理post查询提交
	opt_label = [u'查询', u'请输入关键字进行查询']
	if request.method == 'POST':
		opt = request.form.get('opt','all')
		if opt != 'send_email_password':
			query = query.filter(VulReport.author.like("%" + opt + "%")
									| VulReport.title.like("%" + opt + "%")
									| VulReport.related_asset.like("%" + opt + "%")
									| VulReport.related_asset_inout.like("%" + opt + "%")
									| VulReport.related_asset_status.like("%" + opt + "%")
									| VulReport.related_vul_type.like("%" + opt + "%")
									| VulReport.vul_source.like("%" + opt + "%")
									| VulReport.vul_status.like("%" + opt + "%")
								)
		elif opt=='send_email_password':
			if current_user.role_name==u'超级管理员' or current_user.role_name==u'安全管理员':
				pass

	if current_user.role_name == u'超级管理员' or current_user.role_name == u'安全管理员':
		vul_report_list = query.all()
	elif current_user.role_name == u'安全人员':
		vul_report_list = query.filter(VulReport.author==current_user.email).all()
	elif current_user.role_name == u'普通用户':
		department_list = Depart.query.filter_by(email=current_user.email).all()
		if department_list:
			vul_report_list = []
			for department in department_list:
				vul_report_list += query.filter(Asset.department==department.department).all()
		else:
			vul_report_list = query.filter(Asset.owner.like("%" + current_user.email + "%")).all()
	return render_template('src/vul_finished_list.html', vul_report_list=vul_report_list, opt_label=opt_label)


''' 漏洞报告详情查看页面 '''
@src.route('/vul_report_read/<id>')
def vul_report_read(id):
	vul_report = VulReport.query.get_or_404(id)
	#未完成漏洞和输出文档，需要用户先登录
	if vul_report.vul_status != u'完成' or vul_report.related_vul_type ==u'输出文档':
		if current_user.is_authenticated:
			#未完成漏洞，允许安全人员、安全管理员、超级管理员查看
			if current_user.role_name==u'超级管理员' or current_user.role_name==u'安全管理员' or current_user.role_name==u'安全人员':
				pass
			else:
				#普通用户只允许查看已通告后，并且属于自己的漏洞
				if vul_report.vul_status == u'未审核':
					abort(403)
				else:
					email_dict = get_email_dict(id)
					if (current_user.email not in email_dict['owner']) and (current_user.email != email_dict['department_manager']):
						abort(403)
		else:
			return redirect( url_for('auth.login', next=url_for('src.vul_report_read', id=id)) )
	else:
		#完成漏洞，都可以访问
		pass

	return render_template('src/vul_report_read.html', vul_report=vul_report)


''' 漏洞报告删除功能请求 '''
@src.route('/vul_report_delete/<id>')
@permission_required('src.vul_report_delete')
def vul_report_delete(id):
	vul_report_del = VulReport.query.get_or_404(id)
	db.session.delete(vul_report_del)
	flash(u'删除漏洞报告成功')
	# 删除漏洞报告后，同时删除该漏洞报告的漏洞日志
	query = VulLog.query.filter_by(related_vul_id=id)
	if query.first():
		for vul_log in query.all():
			db.session.delete(vul_log)
			flash(u'删除漏洞日志成功')
	return redirect(url_for('src.vul_report_list_read'))


''' 漏洞报告审核页面 '''
@src.route('/vul_report_review/<id>', methods=['GET','POST'])
@permission_required('src.vul_report_review')
def vul_report_review(id):
	form = VulReportReviewForm()
	vul_report_rv = VulReport.query.get_or_404(id)
	#author_get = User.query.filter_by(name=vul_report_rv.author).first()
	asset_get = Asset.query.filter_by(domain=vul_report_rv.related_asset).first()

	#----------------添加漏洞审核时资产各字段是否填写的判断----------------
	asset_error_flag = 0
	if asset_get.department == '':
		flash(u'资产%s部门不能为空!' %asset_get.domain)
		asset_error_flag = 1
	else:
		department_get = Depart.query.filter_by(department=asset_get.department).first()
		if department_get.email == '':
			flash(u'资产%s部门负责人不能为空!' %asset_get.domain)
			asset_error_flag = 1

	if asset_get.owner == '':
		flash(u'资产%s负责人不能为空!' %asset_get.domain)
		asset_error_flag = 1

	if asset_get.in_or_out == '':
		flash(u'资产%s内外网不能为空!' %asset_get.domain)
		asset_error_flag = 1

	if asset_get.level == '':
		flash(u'资产%s重要程度不能为空!' %asset_get.domain)
		asset_error_flag = 1

	if asset_get.status == '':
		flash(u'资产%s状态不能为空!' %asset_get.domain)
		asset_error_flag = 1

	# 如果资产部分属性没有填写，则跳转到资产查看页面，进行资产属性补充
	if asset_error_flag == 1:
		return redirect(url_for('src.assets_read',opt=asset_get.domain))


	email_dict = get_email_dict(id)
	#Post提交审核完成，发送通告邮件
	if form.validate_on_submit():
		vul_report_rv.related_vul_cata = form.related_vul_cata.data
		vul_report_rv.related_vul_type = form.related_vul_type.data
		vul_report_rv.grant_rank = form.grant_rank.data
		vul_report_rv.start_date = form.start_date.data
		vul_report_rv.end_date = form.end_date.data

		#设置风险值
		risk_score, days = get_risk_score_and_end_date(int(vul_report_rv.grant_rank), asset_get)
		vul_report_rv.risk_score = risk_score

		flash(u'漏洞报告审核成功')

		#更新资产更新时间
		if asset_get.update_date:
			asset_get.update_date = vul_report_rv.start_date
		else:
			asset_get.create_date = vul_report_rv.start_date
			asset_get.update_date = vul_report_rv.start_date

		#发送审核后的漏洞通告邮件
		if vul_report_rv.related_vul_type == u'输出文档':
			vul_report_rv.vul_status = u'完成'
			asset_get.chkdate = form.start_date.data
			to_email_list = []
			for i in email_dict['owner']:
				to_email_list.append(i)
			to_email_list.append(email_dict['department_manager'])
			to_email_list.append(email_dict['author'])
			send_email(u'安全测试输出文档', 'src/email/new_xmind_alert', to=to_email_list, cc=current_app.config['CC_EMAIL'], vul_report_rv=vul_report_rv)
			flash(u'安全测试输出文档-邮件发送成功')
		else:
			to_email_list = []
			for i in email_dict['owner']:
				to_email_list.append(i)
			to_email_list.append(email_dict['department_manager'])
			to_email_list.append(email_dict['author'])
			send_email(u'新漏洞通告', 'src/email/new_vul_alert', to=to_email_list, cc=current_app.config['CC_EMAIL'], vul_report_rv=vul_report_rv)
			flash(u'新漏洞通告邮件发送成功')
			vul_report_rv.vul_status = u'已通告'

		#记录漏洞日志
		vul_log = VulLog(related_vul_id = vul_report_rv.id,
						related_user_email = current_user.email,
						action = u'发送新漏洞通告',
					)
		db.session.add(vul_log)

		return redirect(url_for('src.vul_report_list_read'))

	# 自动计算风险和修复期限
	risk_score, days = get_risk_score_and_end_date(int(vul_report_rv.grant_rank), asset_get)

	#通告日期
	start_date = datetime.date.today()
	
	#限定修复日期
	end_date = datetime.date.today() + datetime.timedelta(days=days)


	form.related_vul_type.data = vul_report_rv.related_vul_type
	form.related_vul_cata.data = vul_report_rv.related_vul_cata
	form.grant_rank.data = str(vul_report_rv.grant_rank)
	form.start_date.data = start_date
	form.end_date.data = end_date
	return render_template('src/vul_report_review.html', form=form, vul_report_rv=vul_report_rv, 
							asset_get=asset_get, email_dict=email_dict, risk_score=risk_score)


''' 漏洞报告审核页面ajax请求处理，根据评定rank自动计算风险值和截止修复期限'''
@src.route('/vul_report_review_ajax/<id>', methods=['POST'])
@permission_required('src.vul_report_review_ajax')
def vul_report_review_ajax(id):
	vul_report_rv = VulReport.query.get_or_404(id)
	asset_get = Asset.query.filter_by(domain=vul_report_rv.related_asset).first()
	risk_score, days = get_risk_score_and_end_date(int(request.form.get('grant_rank')), asset_get)
	end_date = datetime.date.today() + datetime.timedelta(days=days)
	return jsonify(risk_score=str(risk_score), end_date=end_date.strftime('%Y-%m-%d'))


''' “请确认已知悉”按钮功能请求，处理后漏洞状态变更为“修复中” '''
@src.route('/vul_report_known/<id>')
@permission_required('src.vul_report_known')
def vul_report_known(id):
	vul_report = VulReport.query.get_or_404(id)
	if current_user.is_authenticated:
		email_dict = get_email_dict(id)
		# 判断用户是否拥有该漏洞报告权限
		if (current_user.email in email_dict['owner']) or (current_user.email == email_dict['department_manager']):
			if vul_report.vul_status != u'已通告':
				return render_template('src/vul_report_read.html', vul_report=vul_report)
			vul_report.vul_status = u'修复中'
			vul_log = VulLog(related_vul_id=id,
							related_user_email=current_user.email,
							action=u'已知悉',
							)
			db.session.add(vul_log)
			flash(u'已知悉提交成功!')
			#更新资产创建时间和更新时间
			asset_get = Asset.query.filter_by(domain=vul_report.related_asset).first()
			if asset_get.update_date:
				asset_get.update_date = datetime.date.today()
			else:
				asset_get.create_date = datetime.date.today()
				asset_get.update_date = datetime.date.today()

		else:
			abort(403)
	else:
		abort(403)
	
	return render_template('src/vul_report_read.html', vul_report=vul_report)


''' 申请复测按钮功能请求 '''
@src.route('/vul_report_dev_finish/<id>', methods=['GET','POST'])
@permission_required('src.vul_report_dev_finish')
def vul_report_dev_finish(id):
	form = VulReportDevFinishForm()
	vul_report_df = VulReport.query.get_or_404(id)
	if current_user.is_authenticated:
		# 只有修复中和暂不处理状态的漏洞，才可以提交申请复测
		if vul_report_df.vul_status != u'修复中' and vul_report_df.vul_status != u'暂不处理':
			abort(403)
		else:
			email_dict = get_email_dict(id)
			if (current_user.email in email_dict['owner']) or (current_user.email == email_dict['department_manager']) \
				   							or (current_user.role_name == u'超级管理员') \
				   							or (current_user.role_name == u'安全管理员'):
				pass
			else:
				abort(403)
	else:
		abort(403)

	#Post提交复测申请
	if form.validate_on_submit():
		vul_log = VulLog(related_vul_id=id,
						related_user_email=current_user.email,
						action=u'申请复测',
						content=form.dev_finish_solution.data,
						)
		db.session.add(vul_log)
		flash(u'申请测试提交成功！')

		#更新资产时间
		asset_get = Asset.query.filter_by(domain=vul_report_df.related_asset).first()
		if asset_get.update_date:
			asset_get.update_date = datetime.date.today()
		else:
			asset_get.create_date = datetime.date.today()
			asset_get.update_date = datetime.date.today()


		email_dict = get_email_dict(id)
		#成功申请复测后，发送提醒邮件给漏洞相关人员
		to_email_list = email_dict['owner']
		to_email_list.append(email_dict['department_manager'])
		to_email_list.append(email_dict['author'])
		send_email(u'漏洞复测申请', 'src/email/vul_re_test', to=to_email_list, cc=current_app.config['CC_EMAIL'], vul_report_df=vul_report_df)
		flash(u'发送邮件给 %s 成功' %to_email_list[-1])
		vul_report_df.vul_status = u'复测中'
		return redirect(url_for('src.vul_report_list_read'))
	return render_template('src/vul_report_dev_finish.html', form=form, vul_report_df=vul_report_df)


'''  针对单个漏洞报告手动发送邮件提醒，只有管理员可以对漏洞状态为修复中和暂不处理的漏洞发送邮件提醒 '''
@src.route('/vul_report_send_email/<id>', methods=['GET','POST'])
@permission_required('src.vul_report_send_email')
def vul_report_send_email(id):
	form = VulReportSendEmailForm()
	vul_report_se = VulReport.query.get_or_404(id)
	if current_user.is_authenticated:
		if vul_report_se.vul_status != u'修复中' and vul_report_se.vul_status != u'暂不处理':
			abort(403)
		else:
			if (current_user.role_name == u'超级管理员') or (current_user.role_name == u'安全管理员'):
				pass
			else:
				abort(403)
	else:
		abort(403)


	email_dict = get_email_dict(id)
	#Post提交密码发送邮件
	if form.validate_on_submit():
		if form.pwd.data == 'send_email_password':
			#设置发送邮件的列表
			#成功申请复测后，发送提醒邮件给漏洞相关人员
			to_email_list = email_dict['owner']
			to_email_list.append(email_dict['department_manager'])
			to_email_list.append(email_dict['author'])
			send_email(u'修复中漏洞提醒', 
						'src/email/vul_processing_mail_alert', 
						to=to_email_list, 
						cc=current_app.config['CC_EMAIL'], 
						vul_report_se=vul_report_se
						)
			flash(u'发送邮件给 %s 成功' %to_email_list[0])	
		return redirect(url_for('src.vul_report_list_read'))
	return render_template('src/vul_report_send_email.html', form=form, 
								vul_report_se=vul_report_se, 
								email_dict=email_dict,
							)


''' “提交攻击发现结果”功能请求 '''
@src.route('/vul_report_attack_check/<id>', methods=['GET','POST'])
@permission_required('src.vul_report_attack_check')
def vul_report_attack_check(id):
	form = VulReportAttackForm()
	vul_report_attack = VulReport.query.get_or_404(id)
	asset_get = Asset.query.filter_by(domain=vul_report_attack.related_asset).first()

	if form.validate_on_submit():
		vul_report_attack.attack_check = form.attack_check.data


		vul_log = VulLog(related_vul_id=id,
						related_user_email=current_user.email,
						action=u'攻击发现结果提交',
						content=form.attack_check.data,
						)
		db.session.add(vul_log)
		flash(u'攻击发现结果提交成功！')
		return redirect(url_for('src.vul_report_list_read'))

	form.attack_check.data = vul_report_attack.attack_check
	return render_template('src/vul_report_attack_check.html', form=form, 
							vul_report_attack=vul_report_attack, asset_get=asset_get)


''' 漏洞层面提交功能请求 '''
@src.route('/vul_report_vul_cata/<id>', methods=['GET','POST'])
@permission_required('src.vul_report_vul_cata')
def vul_report_vul_cata(id):
	form = VulReportVulCataForm()
	vul_report_vul_cata = VulReport.query.get_or_404(id)
	asset_get = Asset.query.filter_by(domain=vul_report_vul_cata.related_asset).first()

	if form.validate_on_submit():
		vul_report_vul_cata.related_vul_cata = form.related_vul_cata.data

		return redirect(url_for('src.vul_report_list_read'))

	form.related_vul_cata.data = vul_report_vul_cata.related_vul_cata
	return render_template('src/vul_report_vul_cata.html', form=form, 
							vul_report_vul_cata=vul_report_vul_cata, asset_get=asset_get)


''' 复测结果提交页面 '''
@src.route('/vul_report_retest_result/<id>', methods=['GET','POST'])
@permission_required('src.vul_report_retest_result')
def vul_report_retest_result(id):
	form = VulReportRetestResultForm()
	vul_report_retest = VulReport.query.get_or_404(id)
	if vul_report_retest.vul_status != u'复测中':
		abort(403)
	asset_get = Asset.query.filter_by(domain=vul_report_retest.related_asset).first()

	if form.validate_on_submit():
		vul_report_retest.done_rank = form.done_rank.data
		#计算剩余风险值和修复天数
		risk_score, days = get_risk_score_and_end_date(int(vul_report_retest.done_rank), asset_get)
		vul_report_retest.residual_risk_score = risk_score
		
		if days == 0:
			vul_report_retest.fix_date = datetime.date.today()
			vul_report_retest.vul_status = u'完成'
		else:
			vul_report_retest.end_date = vul_report_retest.start_date + datetime.timedelta(days=days)
			vul_report_retest.vul_status = u'修复中'


		vul_log = VulLog(related_vul_id=id,
						related_user_email=current_user.email,
						action=u'复测结果提交',
						content=form.done_solution.data,
						)
		db.session.add(vul_log)
		flash(u'复测结果提交成功！')

		#更新资产创建时间和更新时间
		if asset_get.update_date:
			asset_get.update_date = datetime.date.today()
		else:
			asset_get.create_date = datetime.date.today()
			asset_get.update_date = datetime.date.today()

		email_dict = get_email_dict(id)
		to_email_list = email_dict['owner']
		to_email_list.append(email_dict['department_manager'])
		to_email_list.append(email_dict['author'])
		#成功提交复测结果后，发送提醒邮件给漏洞相关人员
		send_email(u'复测结果已提交', 'src/email/vul_retest_result', to=to_email_list,cc=current_app.config['CC_EMAIL'], vul_report=vul_report_retest, vul_log=vul_log)
		flash(u'发送邮件给 %s 成功' %to_email_list[0])
		return redirect(url_for('src.vul_report_list_read'))

	form.done_rank.data = str(vul_report_retest.done_rank)
	form.end_date.data = vul_report_retest.end_date
	return render_template('src/vul_report_retest_result.html', form=form, 
							vul_report_retest=vul_report_retest, asset_get=asset_get)


''' 复测结果提交ajax,根据重新评估的rank值计算剩余风险和修复期限 '''
@src.route('/vul_report_retest_ajax/<id>', methods=['POST'])
@permission_required('src.vul_report_retest_ajax')
def vul_report_retest_ajax(id):
	vul_report_retest = VulReport.query.get_or_404(id)
	if vul_report_retest.vul_status != u'复测中':
		abort(403)
	asset_get = Asset.query.filter_by(domain=vul_report_retest.related_asset).first()
	done_rank = int(request.form.get('done_rank'))

	risk_score, days = get_risk_score_and_end_date(done_rank, asset_get)

	#限定修复日期
	if days == 0:
		end_date = vul_report_retest.end_date
	else:
		end_date = vul_report_retest.start_date + datetime.timedelta(days=days)

	return jsonify(residual_risk_score=str(risk_score), end_date=end_date.strftime('%Y-%m-%d'))


''' 根据资产的rank值计算风险值和修复天数 '''
def get_risk_score_and_end_date(rank, asset):
	#设置业务等级系数
	asset_level_value = 0
	if asset.level == u'一级':
		asset_level_value = 1
	elif asset.level == u'二级':
		asset_level_value = 0.9
	elif asset.level == u'三级':
		asset_level_value = 0.8
	else:
		asset_level_value = 0.7

	#设置内外网系数
	asset_inout_value = 0
	if asset.in_or_out == u'外网':
		asset_inout_value = 1
	elif asset.in_or_out == u'内网':
		asset_inout_value = 0.8
	else:
		asset_inout_value = 0

	#风险值＝rank * 业务等级系数 ＊ 风险值权重 ＊ 内外网系数
	risk_score = round(rank * asset_level_value * 5 * asset_inout_value,2)

	#计算修复天数
	if 75<risk_score<=100:
		#days = 3-5
		days = round( 5 - (risk_score-75)*0.08, 0)
	elif  50<risk_score<=75:
		#days = 7-10
		days = round( 10 - (risk_score-50)*0.12, 0)
	elif  25<risk_score<=50:
		#days = 14-20
		days = round( 20 - (risk_score-25)*0.24, 0)
	elif  0<risk_score<=25:
		#days = 21-30
		days = round( 30 - (risk_score-0)*0.36, 0)
	else:
		days = 0

	#如果系统为上线前测试，将修复天数延长至1年
	if asset.status == u'上线前' and days != 0:
		days = 365

	return risk_score, days


''' 根据漏洞ID获取相关负责人的邮箱账号 '''
def get_email_dict(vul_report_id):
	vul_report_get = VulReport.query.get_or_404(vul_report_id)
	#author_get = User.query.filter_by(name=vul_report_get.author).first()
	asset_get = Asset.query.filter_by(domain=vul_report_get.related_asset).first()
	department_get = Depart.query.filter_by(department=asset_get.department).first()
	owner_list = asset_get.owner.lower().split(';')
	"""
	email_dict = [(user_get.name, user_get.email),
				(department_get.leader, department_get.email),
				(author_get.name, author_get.email),
				]
	"""
	email_dict = {
					'owner': owner_list,
					'department_manager': department_get.email,
					'author': vul_report_get.author,
				}

	return email_dict


#--------------------积分管理-----------------------------------------

''' 积分查看页面，根据<int:days>参数查询最近days天数内的积分列表 '''
@src.route('/rank_score_list/<int:days>')
def rank_score_list(days):
	query = LoginUser.query.filter(or_(LoginUser.role_name==u'安全人员',LoginUser.role_name==u'安全管理员'))
	list_user_rank_score = []
	if query.first():
		for sec_user in query.all():
			dict_user = {
				'email': sec_user.email,
				'rank': 0,
				'score': 0,
			}
			#查询安全人员是否有提交漏洞
			vul_report_query = VulReport.query.filter_by(author=sec_user.email)
			if vul_report_query.first():
				#有提交漏洞则遍历漏洞报告，计算rank 和 积分
				for vul_report in vul_report_query.all():
					if vul_report.vul_status!=u'未审核':
						if days==0:
							dict_user['rank'] += int(vul_report.grant_rank)
							dict_user['score'] += float(vul_report.risk_score)
						else:
							days_count = datetime.date.today() - vul_report.start_date
							if days_count <= datetime.timedelta(days=days):
								dict_user['rank'] += int(vul_report.grant_rank)
								dict_user['score'] += float(vul_report.risk_score)
			list_user_rank_score.append(dict_user)
	return render_template('src/rank_score_list.html', list_user_rank_score=list_user_rank_score)

#----------------------------查看漏洞报告生命周期日志--------------------------

''' 根据漏洞id查看漏洞日志 '''
@src.route('/vul_report_log/<id>')
@login_required
def vul_report_log(id):
	vul_log_list =VulLog.query.filter_by(related_vul_id=id).all()
	return render_template('src/vul_report_log.html', vul_log_list=vul_log_list)




#------------资产模块-------------------------------------------------------------------------

''' 前台资产查看页面 '''
@src.route('/assets_read', methods=['GET', 'POST'])
@permission_required('src.assets_read')
def assets_read():
	query = Asset.query
	opt = request.args.get('opt','all')
	page = request.args.get('page', 1, type=int)

	if opt=='all':
		pagination = query.order_by(-Asset.update_date).paginate(
                        page, per_page=current_app.config['SRCPM_PER_PAGE'], error_out=False
                        )
		asset_result = pagination.items
	else:
		pagination = query.filter(Asset.sysname.like("%" + opt + "%") 
											| Asset.domain.like("%" + opt + "%")
											| Asset.back_domain.like("%" + opt + "%")
											| Asset.web_or_int.like("%" + opt + "%")
											| Asset.in_or_out.like("%" + opt + "%")
											| Asset.level.like("%" + opt + "%")
											| Asset.secure_level.like("%" + opt + "%")
											| Asset.business_cata.like("%" + opt + "%")
											| Asset.department.like("%" + opt + "%") 
											| Asset.owner.like("%" + opt + "%")
											| Asset.sec_owner.like("%" + opt + "%")
											| Asset.status.like("%" + opt + "%")
											).order_by(-Asset.update_date).paginate(
                        page, per_page=current_app.config['SRCPM_PER_PAGE'], error_out=False
                        )
		asset_result = pagination.items

	return render_template('src/assets_read.html', asset_result=asset_result,
									pagination=pagination,
									opt=opt,)


''' 前台资产增加页面 '''
@src.route('/assets_add', methods=['GET', 'POST'])
@permission_required('src.assets_add')
def assets_add():
	form = AssetForm()
	if form.validate_on_submit():
		a = Asset(sysname=form.sysname.data, 
					domain=form.domain.data, 
					back_domain=form.back_domain.data, 
					web_or_int=form.web_or_int.data, 
					is_http=form.is_http.data, 
					is_https=form.is_https.data,
					in_or_out=form.in_or_out.data,
					level=form.level.data,
					business_cata=form.business_cata.data,
					department=form.department.data,
					owner=form.owner.data,
					sec_owner=form.sec_owner.data,
					status=form.status.data,
					private_data=form.private_data.data,
					count_private_data=form.count_private_data.data,
					down_time=form.down_time.data,
					secure_level=form.secure_level.data,
					ps=form.ps.data,
					#create_date=datetime.date.today(),
					#update_date=datetime.date.today(),
					)
		db.session.add(a)
		flash(u'资产 %s 添加成功' %form.domain.data)
		return redirect(url_for('src.assets_add'))
	return render_template('src/assets_add.html', form=form)


''' 前台资产修改页面 '''
@src.route('/assets_modify/<id>', methods=['GET', 'POST'])
@permission_required('src.assets_modify')
def assets_modify(id):
	form = AssetForm()
	asset_get = Asset.query.get_or_404(id)
	if form.validate_on_submit():
		asset_get.sysname = form.sysname.data

		vul_report_list = VulReport.query.filter_by(related_asset=asset_get.domain)
		#更改资产的域名
		asset_get.domain = form.domain.data
		#更改关联漏洞报告的域名
		if vul_report_list.first():
			for vul_report in vul_report_list:
				vul_report.related_asset = form.domain.data

		#asset_get.root_dir = form.root_dir.data
		asset_get.back_domain = form.back_domain.data
		asset_get.web_or_int = form.web_or_int.data
		asset_get.is_http = form.is_http.data
		asset_get.is_https = form.is_https.data
		asset_get.in_or_out = form.in_or_out.data
		asset_get.level = form.level.data
		asset_get.business_cata = form.business_cata.data
		asset_get.department = form.department.data
		asset_get.owner = form.owner.data
		asset_get.sec_owner = form.sec_owner.data
		asset_get.status = form.status.data
		#asset_get.chkdate = form.chkdate.data
		asset_get.private_data = form.private_data.data
		asset_get.count_private_data = form.count_private_data.data
		asset_get.down_time = form.down_time.data
		asset_get.secure_level = form.secure_level.data
		asset_get.ps = form.ps.data
		if asset_get.update_date:
			asset_get.update_date = datetime.date.today()
		#else:
		#	asset_get.create_date = datetime.date.today()
		#	asset_get.update_date = datetime.date.today()
		flash(u'资产更新成功')
		return redirect(url_for('src.assets_read'))
	form.sysname.data = asset_get.sysname
	form.domain.data = asset_get.domain
	#form.root_dir.data = asset_get.root_dir
	form.back_domain.data = asset_get.back_domain
	form.web_or_int.data = asset_get.web_or_int
	form.is_http.data = asset_get.is_http
	form.is_https.data = asset_get.is_https
	form.in_or_out.data = asset_get.in_or_out
	form.level.data = asset_get.level
	form.business_cata.data = asset_get.business_cata
	form.department.data = asset_get.department
	form.owner.data = asset_get.owner
	form.sec_owner.data = asset_get.sec_owner
	form.status.data = asset_get.status
	#form.chkdate.data = asset_get.chkdate
	form.private_data.data = asset_get.private_data
	form.count_private_data.data = asset_get.count_private_data
	form.down_time.data = asset_get.down_time
	form.secure_level.data = asset_get.secure_level
	form.ps.data = asset_get.ps
	return render_template('src/assets_modify.html', form=form, id = asset_get.id)


''' 前台资产增加ajax请求，根据部门返回部门内用户邮箱列表 '''
@src.route('/assets_add_ajax', methods=['GET','POST'])
@permission_required('src.assets_add_ajax')
def assets_add_ajax():
	department = request.form.get('department')
	user_list = User.query.filter_by(department=department).all()
	opt_list = []
	for user in user_list:
		opt_list.append({'name': user.name, 'email': user.email})
	return jsonify(opt_list)


